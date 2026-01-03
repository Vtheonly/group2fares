from runwayml import RunwayML

import base64
import mimetypes

# Initialize the client with your key
client = RunwayML(
    api_key="key_aa0985f8f51938710c2432635be3ba708ddba652eb24a467191fcf1a32a7a9aebd02a3a8769dedc447b90d92ce3f4f52e7a3636b1f6d8519b76107ab875c2f0e"
)

print("Starting Image+Text to Video generation...")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = 'image/png' # Default or fallback
    return f"data:{mime_type};base64,{encoded_string}"

try:
    image_path = '/home/mersel/Downloads/group2/factory_builder/input/PVB_SGP_Film_Layup_Station.png'
    print(f"Reading image from: {image_path}")
    prompt_image_data = encode_image(image_path)

    # Create the task
    task = client.image_to_video.create(
        model='gen4_turbo',
        prompt_image=prompt_image_data,
        prompt_text="A photorealistic, cinematic drone shot flying through the bright, modern factory floor of 'Complexe Industriel Polymère'. The camera tracks the Safety Glass Lamination line in a seamless flow. We see a pristine glass sheet entering the 12-meter long 'Glass Washing and Drying System', emerging sparkling clean. It moves to the 'PVB Film Layup Station' where precision robotics apply the interlayer. In the background, the massive 15-meter cylindrical 'High-Pressure Lamination Autoclave' looms with steam venting. The scene is high-tech, clean, with volumetric lighting reflecting off the metallic conveyor rollers and glass surfaces. 8k, industrial automation style.",
        ratio='1280:720',
        duration=10,  # Duration in seconds (up to 10 for gen4_turbo)
    )

    print(f"Task created with ID: {task.id}")
    print("Waiting for generation to finish...")

    # Wait for the task to complete
    result = client.tasks.retrieve(id=task.id).wait_for_task_output()

    # Print the result
    print("\nSUCCESS! Video generated.")
    print("Video URL:", result.output[0])

except Exception as e:
    print(f"An error occurred: {e}")
