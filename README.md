# Factors influencing stock option returns: On the Relevance of Systematic and Idiosyncratic Volatility

 [Description]: 
 The classic hedging strategy for options is delta hedging. Here, the option is hedged against changes in the price of the underlying asset by means of an offsetting position in the underlying asset [1]. In the context of the Black-Scholes model, such a strategy has a discounted expected value of zero, e.g. if the position in the underlying is adjusted daily.

Empirically, it has been shown that such a hedging strategy generates a loss on average when an option is purchased [2]. This can be explained by the restrictive assumption of constant volatility of the underlying asset in the Black-Scholes model.

In reality, volatility fluctuates, so that the seller of an option bears the risk of increasing volatility of the underlying. Thus, the negative returns can be interpreted as a volatility risk premium paid by the buyer to the seller for taking on the volatility risk. For options on single stocks, the volatility of the underlying can be divided into a systematic and an idiosyncratic component by means of a corresponding factor model [3].

In this project, the empirical analysis of the cross-section of delta-neutral option returns will be used to investigate the extent to which the volatility risk premium is driven by the two components. In addition, a further breakdown of systematic volatility can be made with respect to systematic risk factors.

# Code Structure

The code is structured as follows:

- `main.ipynb`: The main file to run the code. It is divided into the following sections:

    #### - I. Import and transoform option data:
    - 1 Import and merge option data from .xlsx files as pandasDataFrame 'option_data'
    - 2 Transform stikeprice
    - 3 Calculate optionpirce as midprice of bid and ask
    - 4 Filter option data 30 days before maturity
    - 5 Delete options with more than 6 (>=7) missing deltas
    - 6 Replace deltas if only <7 values are missing
    #### - II. Calculate Delta-Hedged-Gains
    - 1 Calculate delta-hedged-gains for each OptionID
    - 2 Save results in new pandasDataFrame 'delta_gain_returns'
    #### - III. Calculate Idiosyncratic Stock Volatility
    - 1 Import and merge stock data from .xlsx files as pandasDataFrame 'stock_data'
    - 2 Calculate for each OptionID the volatility and standard deviation for the underlying stock (-60 to -30 days before maturity) and split it into idiosyncratic and systematic volatility
    - 3 Save results in new pandasDataFrame 'final_dataset'
    #### - IV. Fama-MacBeth-Regression
    - 1 Calculate descriptive statistics for the final_dataset
    - 2 Calculate regression of the delta-gain-hedge return (dependend variable) on the idiosyncratic volatility and the systematic volatility (independent variables).
    #### - V. Appendix
    - 1 Descriptive statistics for final_dataset sorted by idiosyncratic volatility (top and bottom 20%)
    - 2 Regression with delta-gain-hedge return (dependend variable) on the volatility measured by variance/standard deviation (independent variables).
    - 3 Regression with delta-gain-hedge return (dependend variable) on the idiosyncratic volatility and the systematic volatility (independent variables). Difference to IV (2): This time we use the standard deviation as volatility measure instead of the variance. Additionally we use the same definition of systematic volatility as in the paper [3]. This means, that also the idiosyncratic volatility is calculated differently (residuals in 3-factor model instead of 1-factor).
- `master_functions.py`: Contains all functions used in the main file

# Comments and points to be discussed

Paper [3] says: 
- "delta-hedged equity option return decreases monotonically with an increase in the idiosyncratic volatility of the underlying stock" p.1
- "the coefficient on idiosyncratic volatility remains negative and significant" p.2
- "Total volatility (VOL) is the standard deviation of daily stock returns" Table 1
- "delta-hedged option return is negatively related to the total volatility of the underlying stock, measured as the std.dev of daily stock returns." p.8 
- The VOL coefficient estimate in this situation in the paper is -0.0299; mine is -0.027797 (Table 2)
- "IVOL is in the paper defined as the standard deviation of the resioduals of the Fama-French 3-factors model estimated using the daily stock returns over the previous month" Table 1
- "Systematic Volatility is defined as sqrt(VOL^2 - IVOL^2)" p.9
- "All volatility measures are annualized" <- Wurzel-T-Gesetz reicht aus? Table 2

### Literature:
[1] Black und Scholes (1973): The Pricing of Options and Corporate Liabilities, The Journal of Political Eco- nomy, Jg. 81, S. 637-654.

[2] Bakshi und Kapadia (2003): Delta-hedged gains and the negative market volatility risk premium, Review of Financial Studies Jg. 16, S. 527-566.

[3] Cao und Han (2013): Cross section of option returns and idiosyncratic stock volatility, Journal of Finan- cial Economics Jg. 108, S. 231-249.