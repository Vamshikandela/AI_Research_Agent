
from agents import build_search_agent,build_reader_agent,writer_chain,critic_chain

def run_research_pipeline(topic : str) -> str:
    state={}  ### results are saved in the state / i.e memory 

    #search agent 
    print("\n "+"="*50)
    print("step-1: search_agent is working .....")
    print("="*50)
    search_agent=build_search_agent()
    search_results=search_agent.invoke({"messages":[("user",f"Find recent, reliable and detailed information about: {topic}")]
                         })
    state["search_results"]=search_results['messages'][-1].content
    print("\n search",state['search_results'])


    ## step 2 reader agent
    print("\n "+"="*50)
    print("step-2: Reader agent is working .....")
    print("="*50)
    reader_agent=build_reader_agent()
    reader_result=reader_agent.invoke({
            "messages":[("user",f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
            )]
    })
    state['scraped_content']=reader_result['messages'][-1].content
    print("\n Scraped content\n",state['scraped_content'])

    print("\n "+"="*50)
    print("step-3: writer agent is drafting the report  .....")
    print("="*50)
    research_combined=(
        f"SEARCH RESULTS: \n {state['search_results']} \n\n "
        f"DETAILED SCRAPED CONTENT: \n {state['scraped_content']}"

    )
    state["report"]=writer_chain.invoke({'topic':topic,
                         'research':research_combined})
    print("\n Final Report \n",state['report'])



    ## step3: critic report

    print("\n "+"="*50)
    print("step-4: crtic agent is reviewing the report  .....")
    print("="*50)
    state['feedback']=critic_chain.invoke({"report": state['report']})
    print("\n critic report \n",state['feedback'])
    return state

if __name__=="__main__":
    topic=input("\n Enter a Research Topic: ")
    run_research_pipeline(topic)









