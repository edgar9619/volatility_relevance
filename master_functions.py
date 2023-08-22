"""
Implementing the functions that are used in the main file: "main.ipynb"

"""
import pandas as pd
import numpy as np
import glob
import statsmodels.api as sm

# import and transoform datasets

def import_data(dataset):
    """
    This functions loads the data that was exported from the MS-AccsessDB and merges the data if necessary. 
    The output is saved as a pandas dataframe.
    """
    if dataset == "option_data":
        #import and merge all option data
        path = r'/Users/edgarschmidt/Desktop/Masterarbeit/Datasource/Excel_Export/Option_data'
        all_files = glob.glob(path + "/*.xlsx")
        empty_list = []
        for filename in all_files:
            option_data = pd.read_excel(filename, index_col=None, header=0)
            empty_list.append(option_data)
            print("merge",filename)
        option_data = pd.concat(empty_list, axis=0, ignore_index=True)
        return pd.DataFrame(option_data)
    elif dataset == "stock_data":
        #import and merge all stock data
        path = r'/Users/edgarschmidt/Desktop/Masterarbeit/Datasource/Excel_Export/Stock_data'
        all_files = glob.glob(path + "/*.xlsx")
        empty_list = []
        for filename in all_files:
            stock_data = pd.read_excel(filename, index_col=None, header=0)
            empty_list.append(stock_data)
            print("merge",filename)
        stock_data = pd.concat(empty_list, axis=0, ignore_index=True)
        # there are ca. 2000 out of 11 million missings. We can delete/ignore them.
        stock_data = stock_data[stock_data['TotalReturn']>-1]
        return pd.DataFrame(stock_data)
    elif dataset == "ATM_c_option_m30_all":
        #import excel file with additional option data
        ATM_c_option_m30_all = pd.read_excel('/Users/edgarschmidt/Desktop/Masterarbeit/Datasource/Excel_Export/ATM_c_option_m30_all.xlsx', index_col=None, header=0)
        return pd.DataFrame(ATM_c_option_m30_all)
    else:
        print("Error: no dataset found")


def transform_strikeprice(option_data):
    """
    The original data source has exported a wrong format for the strike price. 
    This function transforms the strike price into the correct format.
    """
    option_data['Strike'] = option_data['Strike']/1000
    return option_data


def calculate_optionprice_C(option_data):
    """
    Later, in the delta-gain-hedge calculation, we need the option price C. 
    This function calculates the option price C as the middle price of best bid and best offer.
    """
    option_data['Optionprice_C'] = round(0.5*(option_data['BestBid']+option_data['BestOffer']),2)
    return option_data


def filter_option_data_30_days_before_maturity(option_data):
    """
    We are only interested in the observations 30 days before maturity. 
    The other observations are not relevant for our analysis and are therefore deleted.
    """
    print("Shape before transformation: ",option_data.shape)
    option_data = option_data[(option_data['Datum'] >= option_data['minus30']) & (option_data['Datum'] <= option_data['maturity'])]
    print("Shape after transformation: ",option_data.shape)
    return option_data
    

def delete_options_with_more_than_x_missings(option_data,x):
    """
    Missing Delta values are indicated with a value of -99,x. This function deletes all options that have more than x missing values.
    """
    # Identifying the OptionIDs that have more than x missing values
    missing_values = option_data['Delta'] < -99.1
    option_ids_to_remove = option_data.loc[missing_values, 'OptionID'].value_counts()
    option_ids_to_remove = option_ids_to_remove[option_ids_to_remove > x].index.tolist()

    # Removing the identified OptionIDs
    option_data = option_data.loc[~option_data['OptionID'].isin(option_ids_to_remove)]
    
    print("Number of deleted options: ", len(option_ids_to_remove))
    return option_data


def replace_missings(option_data):
    """
    If we have less then 7 missing values, we can replace the missing values with the value of the previous day. 
    If there is no previous day, then we are using the next day.
    """
    #replace the missing values (e.g. the -99,x values) with NaN
    #option_data.loc[option_data['Delta'] < -99,'Delta'] = np.nan <- also good solution
    option_data['Delta'] = np.where(option_data['Delta'] < -99, np.nan, option_data['Delta'])
    
    #for each OptionID replace NaN with the value of the previous day. If there is no previous day, then use the next day
    def fill_missing_values(x):
        return x.fillna(method='ffill').fillna(method='bfill')
    
    option_data['Delta'] = option_data.groupby('OptionID')['Delta'].transform(fill_missing_values)

    return option_data


def calculate_discrete_delta_hedged_gains(option_data):
    """
    Calculate Delta-Hedged-Gain-Return for each OptionID in the dataset.
    Return all results in a new table called "delta_gain_table".

    // This implementation uses vectorized operations, which can significantly speed up the calculation 15min -> 1min
    """
    
    option_data['increment_2_part'] = option_data['Delta'] * (option_data['ClosePrice'].shift(-1) - option_data['ClosePrice'])
    option_data['increment_3_part'] = (1/365) * (option_data['date_diff'] * (option_data['interest_rate'] / 100)) * (option_data['Optionprice_C'] - option_data['Delta'] * option_data['ClosePrice'])
    
    def compute_increment(option_group):
        option_group_sorted = option_group.sort_values(by='Datum', ascending=True)
        increment_1 = option_group_sorted['Optionprice_C'].iloc[-1] - option_group_sorted['Optionprice_C'].iloc[0]
        increment_2 = option_group_sorted['increment_2_part'].iloc[:-1].sum()
        increment_3 = option_group_sorted['increment_3_part'].sum()
        scalar = option_group_sorted['Delta'].iloc[0]*option_group_sorted['ClosePrice'].iloc[0]-option_group_sorted['Optionprice_C'].iloc[0]
        return (increment_1 - increment_2 - increment_3)/scalar

    delta_gain_table = option_data.groupby(['OptionID', 'SecurityID', 'Strike','maturity']).apply(compute_increment).reset_index(name='delta_gain')
    return delta_gain_table


def transform_stock_returns(stock_data):
    """
    Transforms the stock data into a dataframe with the dates as index and the stock returns as columns.
    """
    stock_returns = stock_data.pivot(index='Datum', columns='SecurityID', values='TotalReturn')
    print('Dimension after transofrmation: ', stock_returns.shape)
    return stock_returns


def transform_market_factors(stock_data):
    """
    Transform stock_data to a new table with 'Datum' as index and 'mkt', 'SMB', 'HML' and 'WML' as columns
    """
    factor_returns = stock_data[['Datum','mkt','SMB','HML','WML']]
    # make 'Datum' to index
    factor_returns = factor_returns.set_index('Datum')
    print('Dimension:', factor_returns.shape)
    # delete duplicate rows
    factor_returns = factor_returns.drop_duplicates()
    print('Dimension after dropping duplicates: ', factor_returns.shape)
    return factor_returns


def calculate_volatilitys(option_data,stock_data):
    """
    Calculate volatilitys for each OptionID in the dataset.
    Return all results in a new table called "volatility_table".
    """
    stock_returns   = transform_stock_returns(stock_data)
    factor_returns  = transform_market_factors(stock_data)
    #create new columns for volatilitys
    option_data['maturity_minus_60_days']   = option_data['maturity'] - pd.DateOffset(days=60)
    option_data['maturity_minus_30_days']   = option_data['maturity'] - pd.DateOffset(days=30)
    option_data['security_variance']        = None
    option_data['security_std_dev']         = None
    option_data['idiosyncratic_volatility'] = None
    option_data['systematic_volatility']    = None
    option_data['systematic_part_percent']  = None
    option_data['stock_data_available']     = False

    for i in range(len(option_data)):
        security_id = option_data['SecurityID'].iloc[i]
        start_time  = option_data.iloc[i,5]
        end_time    = option_data.iloc[i,6]
        delta_days = (end_time - start_time).days
        
        try:
            # filter stock returns and factor returns (between -60 and -30 days before maturity of the option_id)
            filtered_stock_returns  = stock_returns[security_id][(stock_returns.index >= start_time) & (stock_returns.index <= end_time)]
            filtered_factor_returns = factor_returns.iloc[:,0][(factor_returns.index >= start_time) & (factor_returns.index <= end_time)]

            # if len(filtered_stock_returns) == 0: skip and go to next i
            if len(filtered_stock_returns) == 0:
                continue

            # calculate regression with stock and market returns to get idiosyncratic volatility
            y = filtered_stock_returns
            y = y.reset_index(drop=True)

            X = filtered_factor_returns # market returns
            X = X.reset_index(drop=True)
            X = sm.add_constant(X)

            model = sm.OLS(y,X)
            results = model.fit()

            option_data.iloc[i,7]       = np.var(filtered_stock_returns)*np.sqrt(delta_days) #scaled with sqrt of observation days
            option_data.iloc[i,8]       = np.std(filtered_stock_returns)*np.sqrt(delta_days) #scaled with sqrt of observation days
            option_data.iloc[i,9]       = results.resid.var()#  *np.sqrt(delta_days) # <-idiosyncratic volatility also must also be scaled?
            option_data.iloc[i,10]      = option_data.iloc[i,7] - option_data.iloc[i,9]
            option_data.iloc[i,11]      = round(100*option_data.iloc[i,10]/option_data.iloc[i,7],2)
        except:
            option_data.iloc[i,12]      = True
    
    option_data['security_variance']        = option_data['security_variance'].astype(float)
    option_data['security_std_dev']         = option_data['security_std_dev'].astype(float)
    option_data['idiosyncratic_volatility'] = option_data['idiosyncratic_volatility'].astype(float)
    option_data['systematic_volatility']    = option_data['systematic_volatility'].astype(float)
    option_data['systematic_part_percent']  = option_data['systematic_part_percent'].astype(float)

    return option_data


def descriptive_statistics(option_data):
    """
    This function calculates the descriptive statistics for the option data.
    """
    summary_statistics = option_data[['delta_gain','security_variance','security_std_dev','idiosyncratic_volatility','systematic_volatility','systematic_part_percent']].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).transpose()
    return summary_statistics


def final_regression(option_data,constant):
    """
    This function calculates the regression of the delta-gain-hedge (dependend variable) on the idiosyncratic volatility and the systematic volatility (independent variables).
    """
    if constant == True:
        y = option_data['delta_gain']
        y = y.reset_index(drop=True)

        X = option_data[['idiosyncratic_volatility','systematic_volatility']] # market returns
        X = X.reset_index(drop=True)
        X = sm.add_constant(X)

        model = sm.OLS(y,X)
        results = model.fit()
        risk_premia = pd.DataFrame(results.params)
        print(results.summary())
        print(results.pvalues)
        print('')
        print("Beta factors with constant:")
    else:
        y = option_data['delta_gain']
        y = y.reset_index(drop=True)

        X = option_data[['idiosyncratic_volatility','systematic_volatility']] # market returns
        X = X.reset_index(drop=True)
        #X = sm.add_constant(X)

        model = sm.OLS(y,X)
        results = model.fit()
        risk_premia = pd.DataFrame(results.params)
        print(results.summary())
        print(results.pvalues)
        print('')
        print("Beta factors without constant:")

    return risk_premia


