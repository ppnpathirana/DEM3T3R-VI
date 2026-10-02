"""
================================================================================
FREE AI API SYSTEM TEST SUITE
================================================================================
Tests each configured AI provider individually and tests the automatic failover router.
================================================================================
"""

import os
import sys
import time

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from ai_router import get_router, generate_response, mask_token

def run_test_suite():
    router = get_router()
    
    print("\n" + "=" * 80)
    print("                           FREE AI API SYSTEM TEST")
    print("=" * 80)
    
    # 1. Test each provider individually
    provider_results = {}
    for idx, provider in enumerate(router.providers, 1):
        name = provider.name
        if not provider.is_configured():
            status_text = "NOT CONFIGURED"
            detail = f"(Set {provider.env_key_name} in .env)"
        else:
            test_res = router.test_provider(name)
            if test_res["status"] == "AVAILABLE":
                status_text = "AVAILABLE"
                detail = f"(Model: {test_res.get('model', 'default')})"
            else:
                status_text = "FAILED"
                detail = f"(Error: {test_res.get('error', 'unknown')[:40]}...)"
                
        provider_results[name] = status_text
        print(f" [{idx}] {name:<12}: {status_text:<15} {detail}")
        time.sleep(0.3)

    print("-" * 80)
    
    # 2. System Status Summary
    configured_providers = [p.name for p in router.providers if p.is_configured()]
    primary_name = router.providers[0].name if router.providers else "None"
    total_keys = sum(len(p.get_api_keys()) for p in router.providers)
    
    print(f" Primary provider: {primary_name} ({provider_results.get(primary_name, 'UNKNOWN')})")
    print(f" Fallback system : {'ENABLED' if len(configured_providers) > 1 else 'STANDBY (Single Provider)'}")
    print(f" Multi-key pool  : {total_keys} active key(s) across {len(configured_providers)} provider(s)")
    print("-" * 80)

    # 3. Test Full Automatic Failover Router
    print(" [AI Router Live Integration Test]")
    test_prompt = "Name 3 common crop diseases and a 1-step recovery action for tomato in Sinhala or English."
    print(f" Prompt: \"{test_prompt}\"\n")
    
    try:
        start_t = time.time()
        response = generate_response(test_prompt, temperature=0.3, max_tokens=200)
        elapsed = round(time.time() - start_t, 2)
        
        print("\n--- Response Received ---")
        print(response.strip())
        print("-------------------------")
        print(f" Latency: {elapsed}s")
        print(" AI Router Test  : SUCCESS")
    except Exception as e:
        print(f" AI Router Test  : FAILED ({e})")

    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_test_suite()
