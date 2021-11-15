from modelx.serialize.jsonvalues import *

_formula = None

_bases = [
    ".Data",
    ".Assumptions"
]

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def Policy_Year(t):
    return int((t-1)/12) + 1


def Curr_Age(t):
    age_at_entry = Get_Data_Value("age_at_entry")
    return age_at_entry + Policy_Year(t) - 1


def Ind_Death_Rate(t):
    sex = Get_Data_Value("sex")
    mort_factor = Mortality.at[0, Basis]
    radix_age = max(Mortality_Table.Age)
    age = radix_age if Curr_Age(t) > radix_age else Curr_Age(t)
    ann_rate = (Mortality_Table.query(f"Age == {age}")
                .reset_index().at[0, sex]) * mort_factor
    return 1 - (1-ann_rate)**(1/12)


def Ind_Lapse_Rate(t):
    prem_freq = Get_Data_Value("prem_freq")
    max_policy_year = max(Lapse.Policy_Year)
    policy_year = max_policy_year if Policy_Year(t) > max_policy_year else Policy_Year(t)
    ann_rate = (Lapse.query(f"Policy_Year == {policy_year}")
                .reset_index().at[0, Basis]) * (t % (12/prem_freq) == 0)
    return 1 - (1-ann_rate)**(1/prem_freq)


def Prob_Death(t):
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    else:
        return Prob_IF_E(t-1) * Ind_Death_Rate(t)


def Prob_Lapse(t):
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    else:
        return Prob_IF_E(t-1) * (1 - Ind_Death_Rate(t)) * Ind_Lapse_Rate(t)


def Prob_IF_E(t):
    if t < 0 or t > Get_Data_Value("policy_term") * 12:
        return 0
    elif t == 0:
        return 1
    else:
        return Prob_IF_E(t-1) - Prob_Death(t) - Prob_Lapse(t) 


# ---------------------------------------------------------------------------
# References

Basis = ""