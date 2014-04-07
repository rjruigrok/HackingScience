import webactions

keywords = webactions.parseKeywords("TRIBLER: a social-based peer-to-peer system")
print keywords
output = ""
for keyword in keywords:
    print keyword
