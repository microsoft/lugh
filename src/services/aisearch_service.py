# stubbed out - just returning the user query for now
# TODO ADD REAL IMPLEMENTATION OF AI SEARCH CALL

class AiSearchService:
    def __init__(self):
        pass
    
    async def get_data(self, user_query):
        response = f' in AI Search service with query {user_query}'
        print(response)
        return response