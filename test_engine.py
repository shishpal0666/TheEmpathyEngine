from engine import process

text = "Soon after taking oath, Mr. Shah appointed Sudhan Gurung as Home Minister. Gurung, a key figure during the Gen Z protests, filed a complaint against Mr. Oli and Mr. Lekhak in October."
res = process(text, output_path="static/output.wav")
print("\nGenerated SSML:")
print(res['ssml'])
