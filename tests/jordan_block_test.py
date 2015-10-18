# -*- coding: utf-8; mode: sage -*-

import unittest
from sage.all import ZZ, kronecker_symbol, valuation, gcd, mul, QuadraticForm
from siegel_series.tests.utils import random_even_symm_mat
from siegel_series.impl import (jordan_blocks_odd, jordan_blocks_2,
                                _blocks_to_quad_form)
from siegel_series.jordan_block import _jordan_decomposition_odd_p


def _i_func(q):
    '''Return i(B) in Katsurada's paper.
    '''
    m = ZZ(2) * (q.matrix()) ** (-1)
    i = valuation(gcd(m.list()), ZZ(2))
    m = ZZ(2) ** (-i) * m
    if all(m[a, a] % 2 == 0 for a in range(m.ncols())):
        return - i - 1
    else:
        return - i


def q2_q2_blc(blcs):
    max_expt = blcs[0][0]
    non_diags = ("h", "y")
    unit_diags_first_blc = [qf for expt, qf in blcs
                            if expt == max_expt and qf not in non_diags]
    if len(unit_diags_first_blc) == 1:
        blcs_q2 = blcs[1:]
    else:
        if blcs[0][1] in non_diags:
            blcs_q2 = blcs[1:]
        else:
            blcs_q2 = blcs[2:]
    q2 = _blocks_to_quad_form(blcs_q2, ZZ(2))
    return (q2, blcs_q2)


class JordanBlockTest(unittest.TestCase):

    def assert_jordan_blcs(self, p, mat):
        p = ZZ(p)
        if p == 2:
            blcs = jordan_blocks_2(mat)
        else:
            blcs = jordan_blocks_odd(mat, p)
        q = QuadraticForm(ZZ, ZZ(2) * mat)
        q1 = _blocks_to_quad_form(blcs.blocks, p)
        self.assertTrue(q.has_equivalent_Jordan_decomposition_at_prime(q1, p))

    def test_jordan_decomposition_odd_p(self):
        for _ in range(100):
            S = random_even_symm_mat(5)
            for p in [3, 5, 7]:
                self.assertEqual(
                    kronecker_symbol(
                        mul(_jordan_decomposition_odd_p(S, p)) / S.det(), p),
                    1)

    def assert_jordan_blocks_method(self, p, mat):
        p = ZZ(p)
        if p == 2:
            blcs = jordan_blocks_2(mat)
        else:
            blcs = jordan_blocks_odd(mat, p)
        q = QuadraticForm(ZZ, 2 * mat)
        if p == 2:
            should1 = (q.Gram_det() / blcs.Gram_det()) % 8
        else:
            should1 = kronecker_symbol((q.Gram_det() / blcs.Gram_det()), p)
        self.assertEqual(should1, 1)
        self.assertEqual(
            q.hasse_invariant__OMeara(p), blcs.hasse_invariant__OMeara())
        self.assertEqual(q.dim(), blcs.dim())
        self.assertEqual(q.content().valuation(p), blcs.content_order())

    def test_jordan_blocks_method(self):
        for _ in range(100):
            for s in [random_even_symm_mat(4),
                      random_even_symm_mat(5)]:
                for p in [2, 3, 5, 7]:
                    self.assert_jordan_blocks_method(p, s)

    def test_jordan_blcs(self):
        for _ in range(100):
            m = random_even_symm_mat(5)
            n = random_even_symm_mat(4)
            for p in [2, 3, 5, 7]:
                self.assert_jordan_blcs(p, m)
                self.assert_jordan_blcs(p, n)

    def test_assumption(self):
        '''Test assumption of Theorem 4.1 and 4.2 in Katsurada's paper.
        '''
        for _ in range(100):
            for n in range(4, 11):
                m = random_even_symm_mat(n)
                blcs = jordan_blocks_2(m).blocks
                max_expt = blcs[0][0]
                q2, q2_blc = q2_q2_blc(blcs)
                while len(q2_blc) > 2:
                    self.assertTrue(max_expt >= _i_func(q2) + 1)
                    q2, q2_blc = q2_q2_blc(q2_blc)


suite = unittest.TestLoader().loadTestsFromTestCase(JordanBlockTest)
unittest.TextTestRunner(verbosity=2).run(suite)
