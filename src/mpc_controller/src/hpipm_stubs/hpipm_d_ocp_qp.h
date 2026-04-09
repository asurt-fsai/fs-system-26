/**
 * HPIPM OCP QP Header - Stub
 * 
 * Stub implementation for HPIPM QP structure definitions.
 * Link against the real HPIPM library for actual implementations.
 */

#ifndef HPIPM_D_OCP_QP_H
#define HPIPM_D_OCP_QP_H

#include "hpipm_d_ocp_qp_dim.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque QP structure */
typedef struct hpipm_d_ocp_qp {
    hpipm_d_ocp_qp_dim *dim;
    /* Matrix pointers */
    double **BAbt;  /* Dynamics and affine term */
    double **b;     /* Affine term */
    double **Q;     /* State cost */
    double **S;     /* Cross term */
    double **R;     /* Input cost */
    double **q;     /* Linear state cost */
    double **r;     /* Linear input cost */
    double **C;     /* General constraint: C*x + D*u */
    double **D;     /* General constraint matrix */
    double **lg;    /* General constraint lower bound */
    double **ug;    /* General constraint upper bound */
    /* Bound structures */
    int **idxbx;    /* State bound indices */
    double **lbx;   /* State lower bounds */
    double **ubx;   /* State upper bounds */
    int **idxbu;    /* Input bound indices */
    double **lbu;   /* Input lower bounds */
    double **ubu;   /* Input upper bounds */
} hpipm_d_ocp_qp;

/* Memory size calculation */
int d_ocp_qp_memsize(hpipm_d_ocp_qp_dim *dim);

/* QP creation */
hpipm_d_ocp_qp *d_ocp_qp_create(hpipm_d_ocp_qp_dim *dim, void *mem);

#ifdef __cplusplus
}
#endif

#endif /* HPIPM_D_OCP_QP_H */
