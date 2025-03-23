import pandas as pd
import google.generativeai as genai
import os

# Configure the Gemini API key
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def classify_expenses_batched(df, batch_size=20, model_name="gemini-1.5-flash-latest"):
    """
    Classifies expenses in a Pandas DataFrame using the Gemini API, processing in batches.
    """
    model = genai.GenerativeModel(model_name)
    categories = ["Fixed Expenses", "Annual Expenses", "Food Expenses", "Variable Expenses", "Savings"]

    def classify_batch(business_names):
        prompt = f"""Classify each expense into exactly one of these categories: {', '.join(categories)}
        Rules:
        - Fixed Expenses: All subscriptions (Netflix, YouTube), regular bills
        - Food Expenses: All restaurants, cafes, groceries, food delivery
        - Annual Expenses: Insurance, yearly payments
        - Variable Expenses: One-time purchases, shopping
        - Savings: Investment related

        For each numbered expense below, respond with ONLY the category name, exactly as written above.
        Each response must be on a new line and match the number of input items.

        Expenses to classify:
        """
        for i, name in enumerate(business_names, 1):
            prompt += f"{i}. {name}\n"

        try:
            response = model.generate_content(prompt)
            results = response.text.strip().split('\n')
            
            # Ensure we have exactly the right number of results
            if len(results) != len(business_names):
                print(f"Warning: Got {len(results)} results for {len(business_names)} items. Using defaults.")
                return ["Variable Expenses"] * len(business_names)
            
            # Validate each category
            validated_results = []
            for result in results:
                result = result.strip()
                if result not in categories:
                    validated_results.append("Variable Expenses")
                else:
                    validated_results.append(result)
            
            return validated_results

        except Exception as e:
            print(f"Error classifying batch: {e}")
            return ["Variable Expenses"] * len(business_names)

    # Process in batches
    all_categories = []
    for start_idx in range(0, len(df), batch_size):
        end_idx = min(start_idx + batch_size, len(df))
        batch = df['שם בית העסק'][start_idx:end_idx]
        names_list = batch.astype(str).tolist()
        
        batch_categories = classify_batch(names_list)
        all_categories.extend(batch_categories)
    
    # Assign all categories at once
    df['Category'] = all_categories
    
    return df

# Load and process the data
try:
    df = pd.read_csv("merged_transactions.csv", encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv("merged_transactions.csv", encoding='windows-1255')

# Clean the data
df['שם בית העסק'] = df['שם בית העסק'].fillna('')
df = df[~df['שם בית העסק'].str.contains("סה\"כ עסקאות בגיליון זה:", na=False)]

# Classify the expenses
classified_df = classify_expenses_batched(df)

# Save the results
classified_df.to_csv("classified_expenses_gemini.csv", index=False, encoding='utf-8-sig')
print("Classification complete. Results saved to classified_expenses_gemini.csv")