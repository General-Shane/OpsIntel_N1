# Severity 1 Database Outage

**Target Service**: [[Core Database]]
**Severity**: Sev-1

## Description
This runbook covers the triage and mitigation steps for a total loss of connectivity to the primary database instance.

## Triage Steps
1. Verify the current health metrics in the OPSINTEL Dashboard.
2. Check AWS RDS metrics for the master node (CPU, IOPS).
3. If master is unresponsive, immediately engage the On-Call DBA.

## Mitigation
1. Initiate failover to the standby replica.
2. Update connection string in Secrets Manager if automatic DNS routing fails.
3. Post status update to `#incident-sev1` Slack channel.

## Post-Mortem
Ensure all RCA details are attached to the problem record linked to the [[Core Database]].
