/**
 * HPIPM Dimension Header - Stub
 * 
 * Stub implementation for HPIPM dimension management functions.
 * Link against the real HPIPM library for actual implementations.
 */

#ifndef HPIPM_D_OCP_QP_DIM_H
#define HPIPM_D_OCP_QP_DIM_H

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque dimension structure */
typedef struct hpipm_d_ocp_qp_dim {
    int n_stages;   /* Prediction horizon + 1 */
    int *nx;        /* Number of states per stage */
    int *nu;        /* Number of inputs per stage */
    int *nbx;       /* Number of state bounds per stage */
    int *nbu;       /* Number of input bounds per stage */
    int *ng;        /* Number of general constraints per stage */
    int *nsbx;      /* Number of soft state bounds per stage */
    int *nsbu;      /* Number of soft input bounds per stage */
    int *nsg;       /* Number of soft general constraints per stage */
} hpipm_d_ocp_qp_dim;

/* Memory size calculation */
int d_ocp_qp_dim_memsize(int n_stages);

/* Dimension creation */
hpipm_d_ocp_qp_dim *d_ocp_qp_dim_create(int n_stages, void *mem);

/* Setters for dimension parameters */
void d_ocp_qp_dim_set_nx(int stage, int nx, hpipm_d_ocp_qp_dim *dim);
void d_ocp_qp_dim_set_nu(int stage, int nu, hpipm_d_ocp_qp_dim *dim);

#ifdef __cplusplus
}
#endif

#endif /* HPIPM_D_OCP_QP_DIM_H */
