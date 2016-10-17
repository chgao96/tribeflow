#-*- coding: utf8
'''
Unit tests for the dynamic learning model.
'''
from __future__ import division, print_function

from tribeflow import dataio
from tribeflow import dynamic
from tribeflow.tests import files

from tribeflow.kernels import ECCDFKernel

from tribeflow._eval import quality_estimate
from tribeflow._learn import fast_populate

from numpy.testing import assert_equal
from numpy.testing import assert_almost_equal
from numpy.testing import assert_array_equal
from numpy.testing import assert_array_almost_equal

import numpy as np

def test_correlate_all():
    tstamps, Trace, previous_stamps, Count_zh, Count_sz, count_h, count_z, \
            prob_topics_aux, Theta_zh, Psi_sz, hyper2id, source2id = \
            dataio.initialize_trace(files.SIZE10, 2, 10)
 
    C = dynamic.correlate_counts(Count_zh, Count_sz, count_h, count_z, .1, \
            .1)

    assert_equal((2, 2), C.shape)
    assert C[0, 1] != 0
    assert (np.tril(C) == 0).all()

def test_merge():
    tstamps, Trace, previous_stamps, Count_zh, Count_sz, count_h, count_z, \
            prob_topics_aux, Theta_zh, Psi_sz, hyper2id, source2id = \
            dataio.initialize_trace(files.SIZE10, 2, 10)
     
    kernel = ECCDFKernel()
    kernel.build(Trace.shape[0], Count_zh.shape[0], \
            np.array([1.0, Count_zh.shape[0] - 1]))
    
    Trace[:, 0] = 0
    Trace[:, 1] = 0
    Trace[:, 2] = 0
    Trace[:, 3] = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

    Count_sz[:] = 0
    Count_zh[:] = 0
    count_z[:] = 0
    count_h[:] = 0
    
    fast_populate(Trace, Count_zh, Count_sz, count_h, count_z)
    C = dynamic.correlate_counts(Count_zh, Count_sz, count_h, count_z, .1, \
            .1)
    
    alpha_zh, beta_zs, beta_zd = [0.1] * 3
    a_ptz = 1.0
    b_ptz = Count_zh.shape[0] - 1

    ll_per_z = np.zeros(2, dtype='f8')

    quality_estimate(tstamps, Trace, \
                previous_stamps, Count_zh, Count_sz, count_h, \
                count_z, alpha_zh, beta_zd, ll_per_z, \
                np.arange(Trace.shape[0], dtype='i4'), kernel)
    
    Trace_new, Count_zh_new, Count_sz_new, \
            count_z_new, new_stamps, _ = \
            dynamic.merge(tstamps, Trace, previous_stamps, Count_zh, Count_sz, \
            count_h, count_z, alpha_zh, beta_zs, ll_per_z, kernel)
    
    print(Trace_new)
    print(np.array(new_stamps._get_all(0)))
    assert len(new_stamps._get_all(0)) == 10
    assert Count_zh_new.shape[0] < Count_zh.shape[0]
    assert Count_zh_new.shape[1] == Count_zh.shape[1]

    assert Count_sz_new.shape[0] == Count_sz.shape[0]
    assert Count_sz_new.shape[1] < Count_sz.shape[0]

    assert count_z_new.shape[0] < count_z.shape[0]

def test_split():

    tstamps, Trace, previous_stamps, Count_zh, Count_sz, count_h, count_z, \
            prob_topics_aux, Theta_zh, Psi_sz, hyper2id, source2id = \
            dataio.initialize_trace(files.SIZE10, 2, 10)
    
    alpha_zh, beta_zs, a_ptz, b_ptz = [0.1] * 4
    ll_per_z = np.zeros(2, dtype='f8')

    Trace[:, -1] = 0
    previous_stamps._clear()
    tstamps = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 100, 200, 300, 400, 500]]).T
    tstamps = np.array(tstamps, order='C')
    previous_stamps._extend(0, tstamps[:, 0])
    
    Count_zh = np.zeros(shape=(1, Count_zh.shape[1]), dtype='i4')
    Count_sz = np.zeros(shape=(Count_sz.shape[0], 1), dtype='i4')
    count_z = np.zeros(shape=(1, ), dtype='i4')
    
    fast_populate(Trace, Count_zh, Count_sz, count_h, count_z)
    kernel = ECCDFKernel()
    kernel.build(Trace.shape[0], Count_zh.shape[0], \
            np.array([1.0, Count_zh.shape[0] - 1]))

    ll_per_z = np.zeros(1, dtype='f8')

    quality_estimate(tstamps, Trace, \
                previous_stamps, Count_zh, Count_sz, count_h, \
                count_z, alpha_zh, beta_zs, \
                ll_per_z, np.arange(Trace.shape[0], dtype='i4'), \
                kernel)
    
    Trace_new, Count_zh_new, Count_sz_new, count_z_new, \
            new_stamps, _ = \
            dynamic.split(tstamps, Trace, previous_stamps, Count_zh, Count_sz, \
            count_h, count_z, alpha_zh, beta_zs, \
            ll_per_z, kernel, .5, 0)
    
    assert_array_equal(Trace_new[:, -1], [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    assert_array_equal(new_stamps._get_all(0), [1, 2, 3, 4, 5])
    assert_array_equal(new_stamps._get_all(1), [100, 200, 300, 400, 500])
   
    assert Count_zh_new.shape[0] > Count_zh.shape[0]
    assert Count_zh_new.shape[1] == Count_zh.shape[1]
    assert Count_zh_new[0].sum() == 5
    assert Count_zh_new[1].sum() == 5

    assert Count_sz_new.shape[0] == Count_sz.shape[0]
    assert Count_sz_new.shape[1] > Count_sz.shape[1]
    assert Count_sz_new[:, 0].sum() == 10
    assert Count_sz_new[:, 1].sum() == 10

    assert count_z_new.shape[0] > count_z.shape[0]
    assert count_z_new[0] == 10
    assert count_z_new[1] == 10
