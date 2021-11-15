from modelx.serialize.jsonvalues import *

_formula = None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def Reserve_IF(t):
    pol_term = BE.Get_Data_Value("policy_term")

    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return RES.Reserve_PP(t) * BE.Prob_IF_E(t)


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


def CF_Inc_in_Res(t):
    pol_term = BE.Get_Data_Value("policy_term")

    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return Reserve_IF(t) - Reserve_IF(t-1)


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


def Final_PVFP(t):
    pol_term = BE.Get_Data_Value("policy_term")

    if t < 0 or t > pol_term * 12:
        return 0
    else:
        int_rate = BE.Get_Interest_Rate(t+1)
        return (Final_PVFP(t+1) + CF_Net(t+1)) / (1+int_rate)


# ---------------------------------------------------------------------------
# References

BE = ("Interface", ("..", "BE"), "auto")

RES = ("Interface", ("..", "RES"), "auto")