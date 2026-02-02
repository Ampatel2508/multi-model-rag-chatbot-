from app.services import model_service
print(f"Type: {type(model_service)}")
print(f"Has validate_configuration: {hasattr(model_service, 'validate_configuration')}")
if hasattr(model_service, 'validate_configuration'):
    print("✓ validate_configuration method exists")
    result = model_service.validate_configuration('gemini', 'test', 'fake')
    print(f"Result: {result}")
else:
    print("✗ validate_configuration method NOT found")
    print(f"Available methods: {[x for x in dir(model_service) if not x.startswith('_')]}")
