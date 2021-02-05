import requests

ean = "00000001"
code_39 = "72000097"

q = """mutation insert_barcode{{
  insert_barcodes(
    objects: [
      {{
        ean: {}, 
        code_39: {}
      }}
]
) {{
    returning {{
      id,
      ean,
      code_39,
      created_at
}}
}}
}}""".format(ean, code_39)

u = 'http://192.168.2.13:8080/v1/graphql'

def run(query, url):
    print(query)
    r = requests.post(url, json={'query': query})
    print(r.text)

if __name__ == "__main__":
    try:
        run(q, u)
    except:
        print('Stopped')
