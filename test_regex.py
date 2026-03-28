import re

text = "Soon after taking oath, Mr. Shah appointed Sudhan Gurung. Gurung filed a complaint against Mr. Oli. It is 5 p.m. right now!"

# The original logic:
print("Original:")
sentences = re.split(r'(?<=[.!?])\s+', text.strip())
print(sentences)

# The new logic:
print("\nNew:")
sentences = re.split(r'(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSr)(?<!\bJr)(?<=[.!?])\s+', text.strip())
print(sentences)
