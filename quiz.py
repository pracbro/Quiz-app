import requests

def fetch_categories():
    url = "https://quizapi.io/api/v1/categories"

    params = {
        "apiKey": "U3PTMECFI8rVvphui93imf62DmC13wnYFcgrbFsk",
    }
    
    response = requests.get(url, params=params)

    if response.status_code == 200:
        categories = response.json()
        return categories
    else:
        print(f"Failed to fetch categories: {response.status_code}")
        return []


def fetch_quiz_data(cat_name):
    url = "https://quizapi.io/api/v1/questions"

    params = {
        "apiKey": "U3PTMECFI8rVvphui93imf62DmC13wnYFcgrbFsk",
        "limit": 20,
        "category": cat_name,
        "difficulty": "easy"
    }

    response = requests.get(url, params=params)
    quiz_data = []
    for q in response.json():
        if q.get('correct_answer') is not None:
            valid_answers = {ans_id: ans for ans_id, ans in q['answers'].items() if ans is not None}

            if valid_answers:
                q['answers'] = valid_answers
                quiz_data.append(q)

            if len(quiz_data) == 5:
                break

    return quiz_data
