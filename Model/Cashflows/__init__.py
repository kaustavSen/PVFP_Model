from modelx.serialize.jsonvalues import *

_formula = None

_bases = [
    ".Probabilities"
]

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

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


def CF_Premiums(t):
    return Amt_Premiums(t) * Prob_IF_E(t-1)


def CF_Death_Ben(t):
    pol_term = Get_Data_Value("policy_term")
    if t < 0 or t > pol_term * 12:
        return 0
    else:
        return Get_Data_Value("sum_assured") * Prob_Death(t)


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


def CF_Comm(t):
    max_pol_year_comm = Commission.Policy_Year.max()
    pol_year = max_pol_year_comm if Policy_Year(t) > max_pol_year_comm else Policy_Year(t)

    comm_rate= (Commission
                .query(f"Policy_Year == {pol_year}")
                .reset_index()
                .at[0, "Commission"])

    return CF_Premiums(t) * comm_rate


