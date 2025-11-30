import pandas as pd
import numpy as np

def compute_indicators(df, bb_window=20, bb_std_multiplier=2, atr_window=14):
    """
    Compute Bollinger Bands and ATR for the dataframe.
    Adds to df: 'bb_mid', 'bb_upper', 'bb_lower', 'bb_bandwidth', 'atr'
    """
    # Middle band — simple moving average (SMA)
    df['bb_mid'] = df['close'].rolling(window=bb_window).mean()
    df['bb_std'] = df['close'].rolling(window=bb_window).std(ddof=0)  # population std-dev
    df['bb_upper'] = df['bb_mid'] + bb_std_multiplier * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - bb_std_multiplier * df['bb_std']

    # Bandwidth (normalized width)
    # Handle division by zero if close is 0 (unlikely for BTC but good practice)
    df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid'].replace(0, np.nan)

    # True Range (TR) for ATR
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low']  - df['prev_close']).abs()
    df['true_range'] = df[['tr1','tr2','tr3']].max(axis=1)

    # ATR: rolling mean
    df['atr'] = df['true_range'].rolling(window=atr_window).mean()
    
    # Cleanup intermediate columns
    df.drop(columns=['prev_close', 'tr1', 'tr2', 'tr3', 'true_range'], inplace=True)

    return df

def identify_squeeze_periods(df, bandwidth_threshold_quantile=0.10, atr_threshold_quantile=0.10):
    """
    Identify periods (bars) where both BB-bandwidth and ATR are 'low' — i.e. potential squeeze zones.
    """
    # compute quantile thresholds over the entire loaded history
    # NOTE: In a live system, you'd use a rolling quantile to avoid look-ahead bias.
    # For a static backtest of "historical behavior", global quantiles are often acceptable 
    # to define "what is low for this asset", but rolling is more robust.
    # Let's stick to global for simplicity as per pseudocode, but add a comment.
    
    bw_thresh = df['bb_bandwidth'].quantile(bandwidth_threshold_quantile)
    atr_thresh = df['atr'].quantile(atr_threshold_quantile)

    # mask for squeeze
    squeeze_mask = (df['bb_bandwidth'] <= bw_thresh) & (df['atr'] <= atr_thresh)

    df['squeeze'] = squeeze_mask

    # Mark “start of squeeze” (False -> True)
    df['squeeze_start'] = (~df['squeeze'].shift(1).fillna(False)) & (df['squeeze'])
    
    # Mark "end of squeeze" (True -> False) - this is often when the breakout happens
    df['squeeze_end'] = (df['squeeze'].shift(1).fillna(False)) & (~df['squeeze'])

    return df

def run_breakout_tests(df, hold_periods=[1, 4, 12, 24, 168]):
    """
    For every squeeze_end event (breakout point), measure what happens over next N periods.
    We look at 'squeeze_end' because that's when volatility expands (the breakout).
    Alternatively, we can look at 'squeeze_start' to see what happens *during* the squeeze, 
    but usually traders care about the move *out* of the squeeze.
    
    Let's follow the user's prompt which says "measure subsequent price move".
    The user's pseudocode used 'squeeze_start', but 'squeeze_end' (expansion) is more logical for a breakout.
    However, I will support both or stick to the user's request if they were specific.
    User said: "measure subsequent price move... after squeeze".
    Squeeze start = entering low vol. Squeeze end = leaving low vol (breakout).
    I will use SQUEEZE END as the trigger for the "breakout" analysis.
    """
    results = []
    
    # Iterate through points where the squeeze ENDS (volatility expands)
    # We can also check for price breaking the bands here.
    
    # Let's refine the trigger:
    # A "Breakout" is often defined as Close > Upper Band OR Close < Lower Band.
    # We can check if this happens *during* or *immediately after* a squeeze.
    
    # For this implementation, let's look at every 'squeeze' period, and find the first bar 
    # where price closes outside the bands.
    
    # Identify squeeze regions
    df['squeeze_id'] = (df['squeeze'] != df['squeeze'].shift()).cumsum()
    squeeze_groups = df[df['squeeze']].groupby('squeeze_id')
    
    for squeeze_id, group in squeeze_groups:
        if group.empty:
            continue
            
        # The squeeze period
        start_time = group.index[0]
        end_time = group.index[-1]
        
        # Look for breakout in the next X bars after squeeze ends? 
        # Or did it break out *during* the squeeze (thus ending it)?
        # Usually, the squeeze ends *because* the bands expand, often due to a price move.
        
        # Let's look at the bar immediately following the squeeze end.
        # This is the first bar where Bandwidth > Threshold OR ATR > Threshold.
        
        # Find the index location of the last bar of the squeeze
        try:
            last_idx_loc = df.index.get_loc(end_time)
        except KeyError:
            continue
            
        # The "breakout candle" is often considered the one that expanded the bands.
        # Let's start measuring from the close of the last squeeze bar (entry point) 
        # or the close of the first non-squeeze bar.
        # Let's use the close of the last squeeze bar as the "reference price".
        
        ref_price = group.iloc[-1]['close']
        ref_time = group.index[-1]
        
        # Check direction of breakout (did we close above upper or below lower?)
        # We check the NEXT candle (the one that broke the squeeze)
        if last_idx_loc + 1 >= len(df):
            continue
            
        breakout_candle = df.iloc[last_idx_loc + 1]
        
        # Simple direction check: compare breakout close to squeeze average close
        # or check against bands of the *previous* bar (the tight bands)
        prev_upper = group.iloc[-1]['bb_upper']
        prev_lower = group.iloc[-1]['bb_lower']
        
        direction = 'neutral'
        if breakout_candle['close'] > prev_upper:
            direction = 'up'
        elif breakout_candle['close'] < prev_lower:
            direction = 'down'
        else:
            # Volatility expanded but price didn't break bands? 
            # Could be just ATR expansion without directional move yet.
            # We'll label it 'expansion'
            direction = 'expansion'

        for h in hold_periods:
            end_loc = last_idx_loc + 1 + h
            if end_loc >= len(df):
                continue
                
            end_candle = df.iloc[end_loc]
            end_price = end_candle['close']
            
            pct_change = (end_price - ref_price) / ref_price * 100
            
            # Max excursion
            period_slice = df.iloc[last_idx_loc+1 : end_loc+1]
            max_high = period_slice['high'].max()
            min_low = period_slice['low'].min()
            
            max_up = (max_high - ref_price) / ref_price * 100
            max_down = (min_low - ref_price) / ref_price * 100
            
            results.append({
                'squeeze_end_time': ref_time,
                'breakout_time': breakout_candle.name,
                'direction': direction,
                'hold_period': h,
                'pct_change': pct_change,
                'max_up_pct': max_up,
                'max_down_pct': max_down,
                'squeeze_duration': len(group)
            })

    return pd.DataFrame(results)

def summarize_results(results_df):
    """
    Compute statistics of breakout outcomes.
    """
    if results_df.empty:
        return pd.DataFrame()
        
    # Group by hold_period and direction
    summary = results_df.groupby(['hold_period', 'direction']).agg({
        'pct_change': ['count', 'mean', 'median', 'std', 'min', 'max'],
        'max_up_pct': ['mean', 'max'],
        'max_down_pct': ['mean', 'min']
    })
    
    # Flatten columns
    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    return summary
