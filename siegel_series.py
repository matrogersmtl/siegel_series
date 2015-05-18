# -*- coding: utf-8; mode: sage -*-
'''
Compute Siegel series by using recursive equations given by
Katsurada, `An explicit formula for Siegel series,
American jornal of Mathematics 121 (199),415 - 452.'
'''

from sage.all import (cached_function, QuadraticForm, ZZ, QQ,
                      least_quadratic_nonresidue, legendre_symbol, is_odd,
                      matrix)
from degree2.utils import list_group_by
import operator

@cached_function
def does_2adically_rep_zero(a, b, c):
    '''
    Should a, b, c in [1, 3, 5, 7].
    Returns True if ax^2 + by^2 +cz^2 is 2-adically represents zero
    otherwise False.
    '''
    for x in [0, 1, 4]:
        for y in [0, 1, 4]:
            for z in [0, 1, 4]:
                if (any((w%2 for w in [x, y, z])) and
                    (a * x + b * y + c * z) % 8 == 0):
                    return True
    return False


def _trans_jordan_dec_2(us):
    '''
    us = (u1, ... , un)
    Returns a jordan decomp of diag(us) so that the number of diag elements
    is less that or equal to 2.
    For example,
    x1^2 + x2^2 - x3^2 ~ x1^2 + 2*x1*x2.
    x1^2 + x2^2 + x3^2 ~ 3*x1^2 + 2(x2^2 + x2*x3 + x3^2).
    '''
    hyp2_name = "h"
    y2_name = "y"
    if len(us) <= 2:
        return us
    u1, u2, u3 = us[:3]
    u = u1*u2*u3
    l = _trans_jordan_dec_2(us[3:])
    if does_2adically_rep_zero(u1, u2, u3):
        l.extend([(-u) % 8, hyp2_name])
    else:
        l.extend([(3*u)%8, y2_name])
    l_diag = [a for a in l if a not in [hyp2_name, y2_name]]
    if len(l_diag) <= 2:
        return l
    else:
        l_non_diag = [a for a in l if a in [hyp2_name, y2_name]]
        l1 = _trans_jordan_dec_2(l_diag)
        return l1 + l_non_diag

def jordan_blocks_odd(q, p):
    '''
    p: odd prime,
    q: quadratic form.
    Let q ~ sum p**a_i * b_i * x_i^2 be a jordan decomposition.
    Returns the list of (a_i, b_i) sorted so that a_0 >= a_1 >= ...
    '''
    p = ZZ(p)
    res = []
    u = least_quadratic_nonresidue(p)
    for a, q1 in q.jordan_blocks_by_scale_and_unimodular(p):
        for t in q1.Gram_matrix().diagonal():
            if legendre_symbol(t, p) == 1:
                res.append((a, 1))
            else:
                res.append((a, u))
    return list(reversed(res))


def jordan_blocks_2(q):
    '''
    q: quadratic form.
    Returns a list of tuples (a, b)
    `a' is a integer which represents an exponent.
    `b' corresponds a quadratic form with size <= 2,
    that is, `b' is in [1, 3, 5, 7] or is equal to
    strings 'h' or 'y'.
    If `b' is equal to 'h', then the gram matrix of
    the corresponding quadratic form is equal to
    matrix([[0, 1/2], [1/2, 0]]).
    If `b' is equal to 'y', then the gram matrix of
    the corresponding quadratic form is equal to
    matrix([[1, 1/2], [1/2, 1]]).
    If `b' is in [1, 3, 5, 7], then the corresponding
    gram matrix is equal to matrix([[b]]).
    These tuples are sorted so that a_0 >= a_1 >= ...
    '''
    ls = []
    for a, q1 in q.jordan_blocks_by_scale_and_unimodular(2):
        m = q1.Gram_matrix()
        while not m.is_zero():
            m00 = m[0, 0]
            if is_odd(m00):
                ls.append((a, m00 % 8))
                m = m.submatrix(1, 1)
            elif m00 == 0:
                ls.append((a + 1, "h"))
                m = m.submatrix(2, 2)
            else:
                ls.append((a + 1, "y"))
                m = m.submatrix(2, 2)
    # ls is a list of jordan blocks but it may contain diagonal entries of
    # units of length >= 3.
    # We take another jordan blocks by _trans_jordan_dec_2.
    res = [(a, b) for a, b in ls if isinstance(b, str)]
    diag_elts = [(a, b) for a, b in ls if not isinstance(b, str)]
    for a, us_w_idx in list_group_by(diag_elts, lambda x: x[0]):
        l = _trans_jordan_dec_2([_b for _, _b in us_w_idx])
        for b in l:
            if isinstance(b, str):
                res.append((a + 1, b))
            else:
                res.append((a, b))
    return sorted(res, key=lambda x: -x[0])


def siegel_series_polynomial(B, p):
    '''
    B is a half integral matrix and p is a rational prime.
    It returns the polynomial part of the local Siegel series.
    '''
    q = QuadraticForm(ZZ, B * 2)
    if p == 2:
        blcs = jordan_blocks_2(q)
        return _siegel_series_polynomial_2(blcs)
    else:
        blcs = jordan_blocks_odd(q, p)
        return _siegel_series_polynomial_odd(blcs, p)


def _blocks_to_quad_form(blcs, p):
    h = matrix([[QQ(0), QQ(1)/QQ(2)],
                [QQ(1)/QQ(2), QQ(0)]])
    y = matrix([[QQ(1), QQ(1)/QQ(2)],
                [QQ(1)/QQ(2), QQ(1)]])
    mat_dict = {"h": h, "y": y}
    mats_w_idx = [(idx, mat_dict[qf] if qf in ("h", "y") else matrix([[qf]]))
                  for idx, qf in blcs]
    qfs = [QuadraticForm(ZZ, m * ZZ(2) * p**idx) for idx, m in mats_w_idx]
    return reduce(operator.add, qfs)


def _siegel_series_polynomial_2(blcs):
    max_idx = blcs[0][0]
    first_qfs = [qf for idx, qf in blcs if idx == max_idx]
    unit_diags = [qf for qf in first_qfs if qf not in ["h", "y"]]
    if len(unit_diags) == 1:
        # Use the recursive equation given in Theorem 4.1.
        q = _blocks_to_quad_form(blcs, 2)
        q2 = _blocks_to_quad_form(blcs[1:], 2)

    else:
        pass

def _siegel_series_polynomial_odd(blcs, p):
    pass
