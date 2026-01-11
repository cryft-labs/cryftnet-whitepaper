   
   Fee breakdown:
   - Region A deployment gas: 500,000 gas × Region A gas price
   - Federation fee to Main: 
     - Region B mirroring: 0.01 CRYFT
     - Region C mirroring: 0.01 CRYFT
   - Total: local_gas + 0.02 CRYFT federation fee

2) Region A checkpoint includes deployment event:
   - DeploymentEvent(address=0xToken, code_hash, salt, target_regions=[A,B,C], fee_paid=0.02)

3) Main receives checkpoint and processes:
   - Verifies fee_paid >= required fee for target_regions
   - Records in Federation Registry: {
       address: 0xToken, 
       home_region: A,
       target_regions: [A, B, C],  // Only these regions
       balance_portability: true,
       deployed_regions: [A]       // Initially only A
     }
   - Queues deployment to B and C ONLY (not D or E)

4) Main triggers mirroring to Region B, C:
   - RegionDeployer.mirror() called on B and C
   - Region D and E: no deployment (not in target_regions)

5) Contract now exists at 0xToken on Regions A, B, C
   - Region D and E: contract does NOT exist
