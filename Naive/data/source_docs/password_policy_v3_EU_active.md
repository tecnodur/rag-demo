# EU Password and Authentication Policy

## Summary
EU accounts must use passwords or passphrases with a minimum length of 14 characters, and multifactor authentication (MFA) is required for all remote access. Routine 90-day password rotation is not required; password changes are required when compromise is suspected, credentials are exposed, or Security directs a reset.

## Purpose
This policy establishes the baseline for credential security and authentication across EU operations. It supports stronger account security while reducing unnecessary reset cycles that create helpdesk overhead and unsafe user behavior.

## Scope
This policy applies to:
- EU employees and long-term contractors
- All corporate identity accounts in EU business units
- Applications federated through enterprise authentication
- Remote access channels, including VPN and virtual desktop

## Password and Passphrase Requirements
All EU users must follow these rules:
- Minimum length of 14 characters
- Passphrases are encouraged for memorability and strength
- Credentials must not include names, office location, employee IDs, or predictable patterns
- Reuse of the last 12 passwords is prohibited

Complexity composition rules are handled by the identity platform and may vary by application, but the 14-character minimum remains mandatory.

## Password Change Policy
Mandatory periodic 90-day rotation is not part of this policy. Password change is required when:
- A compromise is suspected
- Credentials appear in a known breach dataset
- Security Operations issues a targeted reset directive
- Platform policy requires a reset due to risk signals

## Multifactor Authentication
MFA is required for all remote access and externally initiated login flows:
- Corporate VPN access requires MFA with approved factor types
- Cloud application sign-in from unmanaged networks requires MFA
- High-privilege administrative actions require step-up authentication

## Recovery and Temporary Access
Account recovery is managed by Service Desk with identity verification:
- Temporary passwords are one-time use only
- First login enforces immediate password or passphrase update
- MFA re-enrollment is required after verified account recovery

## Additional Guidance
Teams should follow these requirements anywhere EU identity standards are enforced, including remote access workflows and federated application sign-in.
