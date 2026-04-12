/**
 * HPIPM OCP QP Solution Header - Stub
 * 
 * Stub implementation for HPIPM QP solution structures.
 * Link against the real HPIPM library for actual implementations.
 */

#ifndef HPIPM_D_OCP_QP_SOL_H
#define HPIPM_D_OCP_QP_SOL_H

#include "hpipm_d_ocp_qp_dim.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque solution structure */
typedef struct hpipm_d_ocp_qp_sol {
    hpipm_d_ocp_qp_dim *dim;
    /* Solution vectors */
    double **x;     /* State trajectory */
    double **u;     /* Control trajectory */
    double **pi;    /* Dual variables for dynamics */
    double **lam;   /* Dual variables for constraints */
    double **t;     /* Slack variables */
} hpipm_d_ocp_qp_sol;

/* Memory size calculation */
int d_ocp_qp_sol_memsize(hpipm_d_ocp_qp_dim *dim);

/* Solution structure creation */
hpipm_d_ocp_qp_sol *d_ocp_qp_sol_create(hpipm_d_ocp_qp_dim *dim, void *mem);

/* Getters for solution components */
void d_ocp_qp_sol_get_x(int stage, double *x, hpipm_d_ocp_qp_sol *sol);
void d_ocp_qp_sol_get_u(int stage, double *u, hpipm_d_ocp_qp_sol *sol);
void d_ocp_qp_sol_get_pi(int stage, double *pi, hpipm_d_ocp_qp_sol *sol);
void d_ocp_qp_sol_get_lam(int stage, double *lam, hpipm_d_ocp_qp_sol *sol);

#ifdef __cplusplus
}
#endif

#endif /* HPIPM_D_OCP_QP_SOL_H */
