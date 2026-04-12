/**
 * HPIPM Timing Header - Stub
 * 
 * Stub implementation for HPIPM timing utilities.
 */

#ifndef HPIPM_TIMING_H
#define HPIPM_TIMING_H

#ifdef __cplusplus
extern "C" {
#endif

#include <time.h>

/* Timing structure */
typedef struct hpipm_timer {
    struct timespec tic;
    struct timespec toc;
} hpipm_timer;

/* Timer functions (stub implementations) */
void hpipm_tic(hpipm_timer *timer);
double hpipm_toc(hpipm_timer *timer);

#ifdef __cplusplus
}
#endif

#endif /* HPIPM_TIMING_H */
