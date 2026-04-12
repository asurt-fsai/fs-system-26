/**
 * HPIPM OCP QP IPM Solver Header - Stub
 * 
 * Stub implementation for HPIPM IPM solver structures and functions.
 * Link against the real HPIPM library for actual implementations.
 */

#ifndef HPIPM_D_OCP_QP_IPM_H
#define HPIPM_D_OCP_QP_IPM_H

#include "hpipm_d_ocp_qp.h"
#include "hpipm_d_ocp_qp_sol.h"

#ifdef __cplusplus
extern "C" {
#endif

/* IPM solver arguments structure */
typedef struct d_ocp_qp_ipm_arg {
    double mu0;         /* Initial barrier parameter */
    double alpha_min;   /* Minimum step size */
    int iter_max;       /* Maximum number of iterations */
    int print_level;    /* Verbosity level */
    double tol_stat;    /* Tolerance for stationarity condition */
    double tol_eq;      /* Tolerance for equality conditions */
    double tol_ineq;    /* Tolerance for inequality conditions */
    double tol_comp;    /* Tolerance for complementarity */
} d_ocp_qp_ipm_arg;

/* IPM workspace structure */
typedef struct d_ocp_qp_ipm_ws {
    /* Internal workspace for IPM solver */
} d_ocp_qp_ipm_ws;

/* Memory size calculations */
int d_ocp_qp_ipm_arg_memsize(int n_stages);
int d_ocp_qp_ipm_ws_memsize(hpipm_d_ocp_qp_dim *dim, d_ocp_qp_ipm_arg *arg);

/* Argument structure initialization */
d_ocp_qp_ipm_arg *d_ocp_qp_ipm_arg_create(int n_stages, void *mem);
void d_ocp_qp_ipm_arg_set_default(int n_stages, d_ocp_qp_ipm_arg *arg);

/* Workspace creation */
d_ocp_qp_ipm_ws *d_ocp_qp_ipm_ws_create(hpipm_d_ocp_qp_dim *dim, 
                                        d_ocp_qp_ipm_arg *arg, void *mem);

/* Main solver function */
int d_ocp_qp_ipm_solve(hpipm_d_ocp_qp *qp, hpipm_d_ocp_qp_sol *sol, 
                       d_ocp_qp_ipm_arg *arg, d_ocp_qp_ipm_ws *ws);

/* Solver info and timings */
int d_ocp_qp_ipm_get_status(d_ocp_qp_ipm_ws *ws);
void d_ocp_qp_ipm_print_stat(FILE *file, hpipm_d_ocp_qp_dim *dim, 
                             d_ocp_qp_ipm_arg *arg, d_ocp_qp_ipm_ws *ws);

#ifdef __cplusplus
}
#endif

#endif /* HPIPM_D_OCP_QP_IPM_H */
