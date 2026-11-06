import asyncio
import sys
import traceback

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

async def main():
    print("==================================================")
    print("OMNIFORGE AUTOMATED VERIFICATION SUITE")
    print("==================================================")

    total_passed = 0
    total_tests = 0

    # Test 1: State Manager
    total_tests += 1
    try:
        from tests.unit.test_state_manager import test_mission_lifecycle
        await test_mission_lifecycle()
        print("  ✓ [PASS] tests.unit.test_state_manager::test_mission_lifecycle")
        total_passed += 1
    except Exception as e:
        print(f"  ✗ [FAIL] test_state_manager: {e}")
        traceback.print_exc()

    # Test 2: Verification Engine
    total_tests += 1
    try:
        from tests.unit.test_verification import test_verification_engine
        await test_verification_engine()
        print("  ✓ [PASS] tests.unit.test_verification::test_verification_engine")
        total_passed += 1
    except Exception as e:
        print(f"  ✗ [FAIL] test_verification: {e}")
        traceback.print_exc()

    # Test 3: Full End-to-End Mission Workflow
    total_tests += 1
    try:
        from tests.integration.test_mission_flow import test_full_mission_flow
        await test_full_mission_flow()
        print("  ✓ [PASS] tests.integration.test_mission_flow::test_full_mission_flow")
        total_passed += 1
    except Exception as e:
        print(f"  ✗ [FAIL] test_mission_flow: {e}")
        traceback.print_exc()

    print("==================================================")
    print(f"RESULTS: {total_passed}/{total_tests} test suites passed!")
    print("==================================================")
    
    if total_passed < total_tests:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
