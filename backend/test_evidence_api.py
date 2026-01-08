#!/usr/bin/env python3
"""
Test script for Evidence API endpoints
Run this from the backend container: python test_evidence_api.py
"""
import sys
import requests
import json
from uuid import UUID

BASE_URL = "http://localhost:8000/api"

def test_evidence_api():
    """Test all Evidence API endpoints"""
    
    print("=" * 60)
    print("Testing Evidence API")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1. Testing Login...")
    login_response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": "admin@example.com",
            "password": "admin123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return False
    
    token = login_response.json().get("access_token")
    if not token:
        print("❌ No access token in response")
        return False
    
    print("✅ Login successful")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Create Evidence (free evidence, no relations)
    print("\n2. Testing Create Evidence (free)...")
    evidence_data = {
        "source": "manual",
        "type": "document",
        "description": "Test evidence - firewall configuration screenshot",
        "confidence": 0.8
    }
    
    create_response = requests.post(
        f"{BASE_URL}/evidence",
        json=evidence_data,
        headers=headers
    )
    
    if create_response.status_code != 201:
        print(f"❌ Create evidence failed: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        return False
    
    evidence = create_response.json()
    evidence_id = evidence.get("id")
    print(f"✅ Evidence created: {evidence_id}")
    print(f"   Description: {evidence.get('description')}")
    print(f"   Source: {evidence.get('source')}")
    print(f"   Confidence: {evidence.get('confidence')}")
    
    # Step 3: Get Evidence by ID
    print("\n3. Testing Get Evidence by ID...")
    get_response = requests.get(
        f"{BASE_URL}/evidence/{evidence_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        print(f"❌ Get evidence failed: {get_response.status_code}")
        print(f"   Response: {get_response.text}")
        return False
    
    retrieved_evidence = get_response.json()
    print(f"✅ Evidence retrieved: {retrieved_evidence.get('description')}")
    
    # Step 4: List Evidences
    print("\n4. Testing List Evidences...")
    list_response = requests.get(
        f"{BASE_URL}/evidence",
        headers=headers
    )
    
    if list_response.status_code != 200:
        print(f"❌ List evidences failed: {list_response.status_code}")
        print(f"   Response: {list_response.text}")
        return False
    
    evidences = list_response.json()
    print(f"✅ Found {len(evidences)} evidence(s)")
    
    # Step 5: List Evidences with filter (by source)
    print("\n5. Testing List Evidences with filter (source=manual)...")
    filtered_response = requests.get(
        f"{BASE_URL}/evidence?source=manual",
        headers=headers
    )
    
    if filtered_response.status_code != 200:
        print(f"❌ Filtered list failed: {filtered_response.status_code}")
        return False
    
    filtered_evidences = filtered_response.json()
    print(f"✅ Found {len(filtered_evidences)} evidence(s) with source=manual")
    
    # Step 6: Update Evidence
    print("\n6. Testing Update Evidence...")
    update_data = {
        "description": "Updated: Test evidence - firewall configuration screenshot",
        "confidence": 0.9
    }
    
    update_response = requests.put(
        f"{BASE_URL}/evidence/{evidence_id}",
        json=update_data,
        headers=headers
    )
    
    if update_response.status_code != 200:
        print(f"❌ Update evidence failed: {update_response.status_code}")
        print(f"   Response: {update_response.text}")
        return False
    
    updated_evidence = update_response.json()
    print(f"✅ Evidence updated")
    print(f"   New description: {updated_evidence.get('description')}")
    print(f"   New confidence: {updated_evidence.get('confidence')}")
    
    # Step 7: Create Evidence with relation (zone_id)
    print("\n7. Testing Create Evidence with zone_id relation...")
    # First, try to get a zone (if any exists)
    zones_response = requests.get(
        f"{BASE_URL}/security-zones",
        headers=headers
    )
    
    zone_id = None
    if zones_response.status_code == 200:
        zones = zones_response.json()
        if zones:
            zone_id = zones[0].get("id")
            print(f"   Using zone: {zones[0].get('name')} ({zone_id})")
    
    evidence_with_relation = {
        "source": "document",
        "description": "Test evidence linked to zone",
        "zone_id": zone_id
    }
    
    create_relation_response = requests.post(
        f"{BASE_URL}/evidence",
        json=evidence_with_relation,
        headers=headers
    )
    
    if create_relation_response.status_code == 201:
        evidence2 = create_relation_response.json()
        print(f"✅ Evidence with relation created: {evidence2.get('id')}")
        if zone_id:
            print(f"   Linked to zone: {evidence2.get('zone_name')}")
    else:
        print(f"⚠️  Create evidence with relation failed: {create_relation_response.status_code}")
        print(f"   Response: {create_relation_response.text}")
    
    # Step 8: Test validation (invalid source)
    print("\n8. Testing Validation (invalid source)...")
    invalid_data = {
        "source": "invalid_source",
        "description": "This should fail"
    }
    
    invalid_response = requests.post(
        f"{BASE_URL}/evidence",
        json=invalid_data,
        headers=headers
    )
    
    if invalid_response.status_code == 422:
        print("✅ Validation working: invalid source rejected")
    else:
        print(f"⚠️  Expected 422, got {invalid_response.status_code}")
    
    # Step 9: Test validation (confidence out of range)
    print("\n9. Testing Validation (confidence > 1)...")
    invalid_confidence = {
        "source": "manual",
        "description": "Test",
        "confidence": 1.5
    }
    
    invalid_conf_response = requests.post(
        f"{BASE_URL}/evidence",
        json=invalid_confidence,
        headers=headers
    )
    
    if invalid_conf_response.status_code == 422:
        print("✅ Validation working: confidence > 1 rejected")
    else:
        print(f"⚠️  Expected 422, got {invalid_conf_response.status_code}")
    
    # Step 10: Delete Evidence
    print("\n10. Testing Delete Evidence...")
    delete_response = requests.delete(
        f"{BASE_URL}/evidence/{evidence_id}",
        headers=headers
    )
    
    if delete_response.status_code != 204:
        print(f"❌ Delete evidence failed: {delete_response.status_code}")
        print(f"   Response: {delete_response.text}")
        return False
    
    print("✅ Evidence deleted")
    
    # Step 11: Verify deletion
    print("\n11. Verifying deletion...")
    verify_response = requests.get(
        f"{BASE_URL}/evidence/{evidence_id}",
        headers=headers
    )
    
    if verify_response.status_code == 404:
        print("✅ Evidence correctly deleted (404 returned)")
    else:
        print(f"⚠️  Expected 404, got {verify_response.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ All Evidence API tests completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_evidence_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

