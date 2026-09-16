# Payment Gateway

**Criticality**: CRITICAL
**Service ID**: SVC_PAYMENT
**Owner**: Payments Team

## Overview
The Payment Gateway is the primary interface for processing customer transactions. It integrates with downstream banking APIs and must maintain 99.99% uptime.

## Dependencies
- [[Core Database]]
- Third-Party Auth Provider

## Related Runbooks
- [[Payment Processing Latency]]
