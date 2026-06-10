# Architecture Notes

This system uses asynchronous choreography. The Order Service does not directly call Inventory, Payment, or Notification. Instead, it publishes an `order.created` event and lets downstream consumers react independently.

## Why Event-Driven?

- Reduces direct service coupling
- Improves fault isolation
- Enables independent scaling of consumers
- Supports replayable event streams
- Allows future services to subscribe without modifying existing services

## Failure Handling

Each consumer wraps processing logic in exception handling. Failed payloads are published to `order.dlq` with the source service and error message.

## Security

The Order Service validates JWT tokens before creating orders. The demo token endpoint is for local testing only and should not be used in production.
