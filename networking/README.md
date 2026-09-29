# Networking

## Reported components

| Component | Intended role | Verification needed |
| --- | --- | --- |
| UniFi Cloud Gateway Max | Routing and gateway policy | Actual routing, DNS and DHCP configuration |
| USW-Pro-XG-8-PoE | Switching and PoE | Pi uplink, power and VLAN membership |
| Raspberry Pi 5 | Application host | Address reservation and service access |
| WireGuard | Remote access | Hosting device, routes and access scope |

Actual links and VLANs have not been inspected. Add a topology diagram after
verification, using generic labels instead of private endpoint details.

## Documentation to capture

- Which device provides DNS and DHCP, and how the Pi keeps a stable address.
- Which services should be reachable locally and through WireGuard.
- Whether guest or IoT networks should be isolated from management services.
- Firewall intent and the tests used to confirm access boundaries.
- A recovery path if remote access fails.

Never commit WireGuard private keys or exported network-controller backups.
Keep the live address plan in a private record; this folder should explain the
design and troubleshooting approach.
