import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



# ---------------------------------------
# PREPARE TEXT
# ---------------------------------------

def prepare_text(row):

    fields = [

        str(row.get("Opportunity", "")),

        str(row.get("Category", "")),

        str(row.get("Organization", ""))

    ]


    return " ".join(fields).lower()



# ---------------------------------------
# MATCH USER PROFILE
# ---------------------------------------

def match_opportunities(df, user_profile):


    if df.empty:

        return df



    df = df.copy()



    # Combine opportunity information

    df["Search_Text"] = df.apply(

        prepare_text,

        axis=1

    )



    documents = (

        df["Search_Text"]

        .tolist()

    )



    documents.append(

        user_profile.lower()

    )



    # Convert text to vectors

    vectorizer = TfidfVectorizer(

        stop_words="english"

    )


    vectors = vectorizer.fit_transform(

        documents

    )



    # Compare user profile with opportunities

    similarity = cosine_similarity(

        vectors[-1],

        vectors[:-1]

    )[0]



    df["Match Score"] = (

        similarity * 100

    ).round(2)



    # Sort highest matches

    df.sort_values(

        by="Match Score",

        ascending=False,

        inplace=True

    )



    df.drop(

        columns=[
            "Search_Text"
        ],

        inplace=True

    )


    return df.reset_index(
        drop=True
    )



# ---------------------------------------
# FILTER BY MINIMUM SCORE
# ---------------------------------------

def filter_matches(df, threshold=20):


    return df[

        df["Match Score"]

        >= threshold

    ]



# ---------------------------------------
# TEST
# ---------------------------------------

if __name__ == "__main__":


    sample = pd.DataFrame({

        "Opportunity":[

            "Microsoft Software Internship",

            "Agriculture Grant Program",

            "AI Research Fellowship"

        ],


        "Category":[

            "Internship",

            "Grant",

            "Fellowship"

        ],


        "Organization":[

            "Microsoft",

            "World Bank",

            "Google"

        ]

    })



    user = (

        "Computer Science student "
        "interested in AI internships"

    )


    result = match_opportunities(

        sample,

        user

    )


    print(result)
