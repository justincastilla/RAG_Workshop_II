from client import es, pp

endpoint_name = "text-inference-endpoint"


def create_endpoint(endpoint_name):
    resp = es.inference.put(
        task_type="text_embedding",
        inference_id=endpoint_name,
        inference_config={
            "service": "elasticsearch",
            "service_settings": {
                "model_id": ".multilingual-e5-small",
                "num_allocations": 1,
                "num_threads": 1,
            },
            "chunking_settings": {
                "strategy": "sentence",
                "max_chunk_size": 25,
                "sentence_overlap": 1,
            },
        },
    )

    return resp


# Check if the inference endpoint already exists
def ep_exists(endpoint_name):
    all_endpoints = es.inference.get()
    endpoints_list = all_endpoints.body.get("endpoints", [])
    return any(ep.get("inference_id") == endpoint_name for ep in endpoints_list)


try:
    # Check if the inference endpoint exists
    exists = ep_exists(endpoint_name)
    # If it does not exist, create it
    if not exists:
        print(f"Inference endpoint '{endpoint_name}' does not exist, creating it...")
        ready = False
        # create inference endpoint
        new_endpoint = create_endpoint(endpoint_name)

        print("\nInference endpoint creation response:\n")
        pp.pprint(new_endpoint.body)
        while not ready:
            exists = ep_exists(endpoint_name)
            if exists:
                ready = True
            else:
                print("Waiting for inference endpoint to be created...")
                import time

                time.sleep(5)
    else:
        print(
            f"Inference endpoint '{endpoint_name}' already exists, skipping creation."
        )


except Exception as e:
    print(f"Error checking inference endpoints: {e}")
