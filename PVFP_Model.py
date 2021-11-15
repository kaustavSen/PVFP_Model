import modelx as mx
import pandas as pd

mx.new_model("PVFP_Model")

# Data UserSpace to store the policy data
Data = mx.new_space("Data")

# References
Data.MP_Num = 1

# Reading in the data and storing it as part of the model
Data.new_pandas(name="Policy_Data",
                path="Data/Policy_Data.csv",
                data=pd.read_csv("Policy_Data.csv"),
                filetype="csv")

# Creating a general function to retrive policy data details
@mx.defcells(Data) 
def Get_Data_Value(Data_Var):
    return Policy_Data.query(f"policy_id == {MP_Num}").reset_index().at[0, Data_Var]

# Assumptions UserSpace to store the projecion assumption for both
# BE (Best Estimate) and RES (Reserving) basis
Assumptions = mx.new_space("Assumptions")

Assumptions.new_pandas(name="Mortality",
                       path="Assumptions/Mortality.xlsx",
                       data=pd.read_excel("Assumptions.xlsx", sheet_name="Mortality"),
                       filetype="excel")

Assumptions.new_pandas(name="Mortality_Table",
                       path="Assumptions/Mortality_Table.xlsx",
                       data=pd.read_excel("Assumptions.xlsx", sheet_name="Mortality_Table"),
                       filetype="excel")

Assumptions.new_pandas(name="Lapse",
                       path="Assumptions/Lapse.xlsx",
                       data=pd.read_excel("Assumptions.xlsx",
                                          sheet_name="Lapse"),
                       filetype="excel")

Assumptions.new_pandas(name="Expense",
                       path="Assumptions/Expense.xlsx",
                       data=pd.read_excel("Assumptions.xlsx",
                                          sheet_name="Expense"),
                       filetype="excel")

Assumptions.new_pandas(name="Commission",
                       path="Assumptions/Commission.xlsx",
                       data=pd.read_excel("Assumptions.xlsx",
                                          sheet_name="Commission"),
                       filetype="excel")

Assumptions.new_pandas(name="Interest_Rate",
                       path="Assumptions/Interest_Rate.xlsx",
                       data=pd.read_excel("Assumptions.xlsx",
                                          sheet_name="Interest_Rate"),
                       filetype="excel")

# Probabilities UserSpace to store all the probability calculations
# This is meant to be used as a "base" class for creating other UserSpaces
Probabilities = mx.new_space("Probabilities")

# Define parameters
Probabilities.add_bases(Data)
Probabilities.add_bases(Assumptions)
Probabilities.Basis = "" # can be either BE or RES

@mx.defcells(Probabilities)
def Policy_Year(t):
    return int((t-1)/12) + 1

@mx.defcells(Probabilities)
def Curr_Age(t):
    age_at_entry = Get_Data_Value("age_at_entry")
    return age_at_entry + Policy_Year(t) - 1

@mx.defcells(Probabilities)
def Ind_Death_Rate(t):
    sex = Get_Data_Value("sex")
    mort_factor = Mortality.at[0, Basis]
    radix_age = max(Mortality_Table.Age)
    age = radix_age if Curr_Age(t) > radix_age else Curr_Age(t)
    ann_rate = (Mortality_Table.query(f"Age == {age}")
                .reset_index().at[0, sex]) * mort_factor
    return 1 - (1-ann_rate)**(1/12)

@mx.defcells(Probabilities)
def Ind_Lapse_Rate(t):
    prem_freq = Get_Data_Value("prem_freq")
    max_policy_year = max(Lapse.Policy_Year)
    policy_year = max_policy_year if Policy_Year(t) > max_policy_year else Policy_Year(t)
    ann_rate = (Lapse.query(f"Policy_Year == {policy_year}")
                .reset_index().at[0, Basis]) * (t % (12/prem_freq) == 0)
    return 1 - (1-ann_rate)**(1/prem_freq)

@mx.defcells(Probabilities)
def Prob_Death(t):
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    else:
        return Prob_IF_E(t-1) * Ind_Death_Rate(t)

@mx.defcells(Probabilities)
def Prob_Lapse(t):
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    else:
        return Prob_IF_E(t-1) * (1 - Ind_Death_Rate(t)) * Ind_Lapse_Rate(t)

@mx.defcells(Probabilities)
def Prob_IF_E(t):
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    elif t == 0:
        return 1
    else:
        return Prob_IF_E(t-1) - Prob_Death(t) - Prob_Lapse(t) 
    
# Cashflows UserSpace to store all the cashflow calculations
# This is meant to be used as a "base" class for creating other UserSpaces
# such as the BE and RES layers.
Cashflows = mx.new_space("Cashflows")

# Define references
Cashflows.add_bases(Probabilities)

@mx.defcells(Cashflows)
def Get_Interest_Rate(t):
    max_year = Interest_Rate.Year.max()
    pol_year = max_year if Policy_Year(t) > max_year else Policy_Year(t)
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    else:
        ann_rate = (Interest_Rate
                    .query(f"Year == {pol_year}")
                    .reset_index()
                    .at[0, Basis])
        mth_rate = (1 + ann_rate)**(1/12) - 1
        return mth_rate

@mx.defcells(Cashflows)
def Amt_Premiums(t):
    prem_freq = Get_Data_Value("prem_freq")
    prem_term = Get_Data_Value("prem_term")
    annual_prem = Get_Data_Value("annual_prem")
    
    if t < 0 or t > prem_term * 12:
        return 0
    elif (t-1) % (12/prem_freq) == 0:
        return annual_prem / prem_freq
    else:
        return 0
    
@mx.defcells(Cashflows)
def CF_Premiums(t):
    return Amt_Premiums(t) * Prob_IF_E(t-1)

@mx.defcells(Cashflows)
def CF_Death_Ben(t):
    pol_term = Get_Data_Value("policy_term")
    if t < 0 or t > pol_term * 12:
        return 0
    else:
        return Get_Data_Value("sum_assured") * Prob_Death(t)

@mx.defcells(Cashflows)
def CF_Init_Exp(t):
    init_exp_fixed = (Expense
                      .query("Type == 'Initial_Expense_Per_Policy'")
                      .reset_index()
                      .at[0, Basis])
    
    init_exp_prem = (Expense
                      .query("Type == 'Initial_Expense_Prem'")
                      .reset_index()
                      .at[0, Basis])
    
    if t > 0 and t <= 12:
        return (  init_exp_fixed * (t == 1) 
                + init_exp_prem * CF_Premiums(t))
    else:
        return 0

@mx.defcells(Cashflows)
def CF_Ren_Exp(t):
    pol_term = Get_Data_Value("policy_term")
    
    ren_exp_fixed = (Expense
                      .query("Type == 'Renewal_Expense_Per_Policy'")
                      .reset_index()
                      .at[0, Basis])
    
    ren_exp_prem = (Expense
                      .query("Type == 'Renewal_Expense_Prem'")
                      .reset_index()
                      .at[0, Basis])
    
    ann_infl_rate = (Expense
                      .query("Type == 'Expense_Inflation'")
                      .reset_index()
                      .at[0, Basis])
    
    mth_infl_rate = (1 + ann_infl_rate)**(1/12) - 1
    infl_factor = (1 + mth_infl_rate)**(t-1)
    
    if t < 0 or t > pol_term * 12:
        return 0
    else:
        return (  ren_exp_fixed / 12 * infl_factor * Prob_IF_E(t-1) 
                + ren_exp_prem * CF_Premiums(t))

@mx.defcells(Cashflows)
def CF_Comm(t):
    max_pol_year_comm = Commission.Policy_Year.max()
    pol_year = max_pol_year_comm if Policy_Year(t) > max_pol_year_comm else Policy_Year(t)
    
    comm_rate= (Commission
                .query(f"Policy_Year == {pol_year}")
                .reset_index()
                .at[0, "Commission"])
    
    return CF_Premiums(t) * comm_rate

# BE UserSpace to store all the Best Estiamte calculations
BE = mx.new_space("BE")

# Define all references
BE.add_bases(Cashflows)
BE.Basis = "BE"

# RES UserSpace to store all the Reserving calculations
# and finally compute the projected per-policy reserve
RES = mx.new_space("RES")

# Define all references
RES.add_bases(Cashflows)
RES.Basis = "RES"

@mx.defcells(RES)
def CF_Net_BOP(t):
    pol_term = Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return (  CF_Comm(t)
                + CF_Init_Exp(t)
                + CF_Ren_Exp(t)
                - CF_Premiums(t))

@mx.defcells(RES)
def CF_Inv_Income(t):
    pol_term = Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return CF_Net_BOP(t) * Get_Interest_Rate(t)
    
@mx.defcells(RES)
def Reserve_IF(t):
    pol_term = Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        net_cf = (  CF_Net_BOP(t+1)
                  + CF_Inv_Income(t+1)
                  + CF_Death_Ben(t+1))
        return (net_cf + Reserve_IF(t+1)) / (1 + Get_Interest_Rate(t+1))
    
@mx.defcells(RES)
def Reserve_PP(t):
    pol_term = Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return Reserve_IF(t) / Prob_IF_E(t)

# PVFP UserSpace for the final calculations pulling in values from both
# the BE and RES UserSpaces
PVFP = mx.new_space("PVFP")
PVFP.BE = BE
PVFP.RES = RES

@mx.defcells(PVFP)
def Reserve_IF(t):
    pol_term = BE.Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return RES.Reserve_PP(t) * BE.Prob_IF_E(t)

@mx.defcells(PVFP)
def CF_Inv_Income(t):
    pol_term = BE.Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        bop_net_cashflows = (  BE.CF_Premiums(t)
                             - BE.CF_Init_Exp(t)
                             - BE.CF_Ren_Exp(t)
                             - BE.CF_Comm(t))
        
        int_rate = BE.Get_Interest_Rate(t)
        inv_income = (bop_net_cashflows + Reserve_IF(t-1)) * int_rate
        return inv_income
        
@mx.defcells(PVFP)
def CF_Inc_in_Res(t):
    pol_term = BE.Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return Reserve_IF(t) - Reserve_IF(t-1)

@mx.defcells(PVFP)
def CF_Net(t):
    pol_term = BE.Get_Data_Value("policy_term")
    
    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return (  BE.CF_Premiums(t)
                - BE.CF_Init_Exp(t)
                - BE.CF_Ren_Exp(t)
                - BE.CF_Comm(t)
                - BE.CF_Death_Ben(t)
                - CF_Inc_in_Res(t)
                + CF_Inv_Income(t))

@mx.defcells(PVFP)
def Final_PVFP(t):
    pol_term = BE.Get_Data_Value("policy_term")
    
    if t < 0 or t > pol_term * 12:
        return 0
    else:
        int_rate = BE.Get_Interest_Rate(t+1)
        return (Final_PVFP(t+1) + CF_Net(t+1)) / (1+int_rate)
    
# Generating and saving output for checking purposes.
PVFP.Final_PVFP(0)
PVFP.Final_PVFP.series.sort_index().to_csv("Test.csv")
