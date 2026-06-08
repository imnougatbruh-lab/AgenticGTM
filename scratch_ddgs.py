from ddgs import DDGS

def test_search():
    try:
        with DDGS() as ddgs:
            print("Twitter:")
            results = list(ddgs.text('site:twitter.com "SaaS marketing"', max_results=5))
            for r in results:
                print(r)
                
            print("\nReddit:")
            results2 = list(ddgs.text('site:reddit.com/r/SaaS "SaaS marketing"', max_results=5))
            for r in results2:
                print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
