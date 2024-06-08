import chromadb
import json
import os
import chromadb.utils.embedding_functions as embedding_functions



#using OpenAI embeddings here
embedding_func = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)


add=False
delete_collection=False

chroma_client = chromadb.PersistentClient(path="./chroma_data")

if(delete_collection):
    chroma_client.delete_collection('categories_collection')

# Create or load a collection
collection_name = 'categories_collection'

collections_now_in_db = []
for i in chroma_client.list_collections():
    collections_now_in_db.append(i.name)

if collection_name not in collections_now_in_db:
    print('we are here'.upper())
    collection = chroma_client.create_collection(name=collection_name, embedding_function=embedding_func)
else:
    print('we are here')
    collection = chroma_client.get_collection(name=collection_name,embedding_function=embedding_func)
    print('we are here2')
print('created')

# Example categories and subcategories
categories_data = {
    "Electronics": ["Smartphones", "Laptops", "Tablets"],
    "Home Appliances": ["Refrigerators", "Microwaves", "Washing Machines"],
    "Books": ["Fiction", "Non-Fiction", "Children's Books"]
}


# Function to add categories and subcategories to the collection
def add_categories_to_collection(categories_data, collection):
    print('this got executed')
    for category, subcategories in categories_data.items():
        # Add category
        collection.add(
            documents=[category],
            metadatas=[{"type": "category"}],
            ids=[category]
        )
        # Add subcategories
        for subcategory in subcategories:
            collection.add(
                documents=[subcategory],
                metadatas=[{"type": "subcategory", "parent_category": category}],
                ids=[f"{category}::{subcategory}"]
            )


# Add the categories and subcategories to the collection
if(add):
    add_categories_to_collection(categories_data, collection)
    print('added items')


# Function to perform semantic search
def semantic_search(query, collection, top_k=5):
    #     query_embedding = embedding_func.embed([query])[0]
    query_embedding = embedding_func.embed_with_retries([query])[0]

    # Search for the closest category
    category_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"type": "category"}
    )

    # If there are no category results, return an empty response
    if not category_results['documents']:
        return {"categories": [], "subcategories": []}

    # Get the best matching category
    best_category = category_results['documents'][0][0]
    print(best_category)

    # Search for subcategories within the best matching category
    subcategory_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        #         where={"type": "subcategory", "parent_category": best_category}
        where={"$and": [{"type": "subcategory"}, {"parent_category": best_category}]}
    )

    best_subcategory = subcategory_results['documents'][0][0]
    print(best_subcategory)

    return {
        "categories": best_category,
        "subcategories": best_subcategory
    }



query = "star wars"
results = semantic_search(query, collection)

# Print the results
print(json.dumps(results, indent=2))