import json
from django.conf import settings
from django.db import transaction
from apps.academics.models import Subject, Topic
from .llm import AIUnavailable, generate_text
from .gemini import GeminiUnavailable, generate_text_with_gemini
from .rag import retrieve
from ..models import GeneratedQuestion, GeneratedTest


def _local_questions(topic, count, sources):
    questions = [
        {
            'question': 'What is the primary goal of clustering in machine learning?',
            'options': ['Group similar data points together without labels', 'Predict a continuous output variable', 'Classify data into predefined categories', 'Reduce the number of features in a dataset'],
            'correct_answer': 'Group similar data points together without labels',
            'explanation': 'Clustering is an unsupervised learning technique that groups similar data points together based on their features, without using predefined labels.',
            'source_ids': sources,
        },
        {
            'question': 'Which of the following algorithms is an example of a partitioning-based clustering method?',
            'options': ['K-Means', 'DBSCAN', 'Agglomerative Clustering', 'Gaussian Mixture Model'],
            'correct_answer': 'K-Means',
            'explanation': 'K-Means is a partitioning-based algorithm that divides data into K clusters by minimizing intra-cluster variance.',
            'source_ids': sources,
        },
        {
            'question': 'In K-Means clustering, what does the "K" represent?',
            'options': ['The number of clusters to form', 'The number of features in the dataset', 'The number of iterations the algorithm runs', 'The maximum distance between two points'],
            'correct_answer': 'The number of clusters to form',
            'explanation': 'K is a hyperparameter that specifies how many clusters the algorithm should partition the data into.',
            'source_ids': sources,
        },
        {
            'question': 'What is the Elbow Method used for in clustering?',
            'options': ['Determining the optimal number of clusters K', 'Measuring the accuracy of a clustering model', 'Selecting the best distance metric', 'Initializing cluster centroids randomly'],
            'correct_answer': 'Determining the optimal number of clusters K',
            'explanation': 'The Elbow Method plots inertia (within-cluster sum of squares) vs K values; the "elbow" point where the rate of decrease sharply slows down suggests the optimal K.',
            'source_ids': sources,
        },
        {
            'question': 'DBSCAN clustering is best suited for which type of data?',
            'options': ['Data with arbitrary shapes and noise/outliers', 'Linearly separable data', 'High-dimensional sparse data only', 'Data with a fixed known number of clusters'],
            'correct_answer': 'Data with arbitrary shapes and noise/outliers',
            'explanation': 'DBSCAN (Density-Based Spatial Clustering of Applications with Noise) identifies clusters of arbitrary shape and marks outliers as noise, making it robust to irregular data.',
            'source_ids': sources,
        },
        {
            'question': 'Which metric is commonly used to evaluate the quality of clustering results internally?',
            'options': ['Silhouette Score', 'F1 Score', 'Mean Squared Error', 'ROC-AUC'],
            'correct_answer': 'Silhouette Score',
            'explanation': 'The Silhouette Score measures how similar a point is to its own cluster compared to other clusters. Ranges from -1 to 1; higher is better.',
            'source_ids': sources,
        },
        {
            'question': 'What does inertia measure in K-Means clustering?',
            'options': ['Sum of squared distances from each point to its cluster centroid', 'Number of misclassified data points', 'Total distance between cluster centroids', 'Variance of the feature values'],
            'correct_answer': 'Sum of squared distances from each point to its cluster centroid',
            'explanation': 'Inertia (within-cluster sum of squares) measures how internally coherent clusters are. Lower inertia means tighter, more compact clusters.',
            'source_ids': sources,
        },
        {
            'question': 'In hierarchical clustering, what does a dendrogram represent?',
            'options': ['A tree diagram showing the sequence of cluster merges or splits', 'A scatter plot of clustered data points', 'A bar chart of cluster sizes', 'A heatmap of feature correlations'],
            'correct_answer': 'A tree diagram showing the sequence of cluster merges or splits',
            'explanation': 'A dendrogram visualizes the hierarchical relationship between clusters, showing at what distance clusters were merged (agglomerative) or split (divisive).',
            'source_ids': sources,
        },
        {
            'question': 'Which of the following is a key disadvantage of K-Means clustering?',
            'options': ['It requires specifying K in advance and is sensitive to outliers', 'It cannot handle numerical data', 'It always produces overlapping clusters', 'It is only applicable to binary classification'],
            'correct_answer': 'It requires specifying K in advance and is sensitive to outliers',
            'explanation': 'K-Means requires K to be predefined and its centroid-based approach makes it sensitive to outliers, which can significantly distort cluster positions.',
            'source_ids': sources,
        },
        {
            'question': 'What are the two key parameters in DBSCAN?',
            'options': ['Epsilon (ε) and MinPts', 'K and iterations', 'Alpha and beta', 'Learning rate and momentum'],
            'correct_answer': 'Epsilon (ε) and MinPts',
            'explanation': 'Epsilon defines the radius of the neighbourhood around a point, and MinPts is the minimum number of points required within that radius to form a dense region (core point).',
            'source_ids': sources,
        },
    ]
    return questions[:count]

def _adaptive_difficulty(topic, requested):
    if requested: return requested
    if topic is None: return 'MEDIUM'
    if topic.mastery_percentage < 40: return 'EASY'
    if topic.mastery_percentage < 70: return 'MEDIUM'
    return 'HARD'

def generate_assessment(user, subject_id, topic_id=None, difficulty='MEDIUM', question_count=5, resource_ids=None):
    subject = Subject.objects.filter(id=subject_id, semester__student=user).first()
    if not subject: raise ValueError('Subject not found.')
    topic = Topic.objects.filter(id=topic_id, subject=subject).first() if topic_id else subject.topics.order_by('mastery_percentage').first()
    difficulty = _adaptive_difficulty(topic, difficulty)
    topic_name = topic.name if topic else subject.name
    
    if resource_ids:
        from ..models import ResourceChunk
        chunks = list(ResourceChunk.objects.filter(student=user, resource_id__in=resource_ids).order_by('?')[:15])
    else:
        chunks = retrieve(user, f'practice questions for {topic_name}', subject_id=subject.id, top_k=4)
        
    source_ids = [str(chunk.resource_id) for chunk in chunks]
    questions = None
    context_text = ' '.join(chunk.text for chunk in chunks)
    prompt = (
        f'You are a university exam question generator. Generate exactly {question_count} multiple-choice questions '
        f'based STRICTLY on the following academic notes. Each question must be specific to the content provided. '
        f'Return ONLY a valid JSON array. Each item must have: "question" (string), "options" (array of 4 strings), '
        f'"correct_answer" (one of the options), "explanation" (string). '
        f'Do not add any text before or after the JSON array.'
    )
    context_input = f'Subject: {subject.name}\nTopic: {topic_name}\n\nNotes content:\n{context_text[:6000]}'

    if settings.OPENAI_API_KEY:
        try:
            raw = generate_text(prompt, context_input)
            questions = json.loads(raw)
        except Exception:
            questions = None

    if not isinstance(questions, list) or not questions:
        try:
            raw = generate_text_with_gemini(prompt, context_input)
            # Strip markdown code fences if present
            raw = raw.strip()
            if '```' in raw:
                # Extract content between code fences
                parts = raw.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        part = part[4:].strip()
                    if part.startswith('[') or part.startswith('{'):
                        raw = part
                        break
            questions = json.loads(raw)
        except GeminiUnavailable as exc:
            import logging
            logging.getLogger(__name__).error('Gemini unavailable for assessment: %s', exc)
            questions = None
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error('Gemini assessment parse error: %s', exc)
            questions = None

    if not isinstance(questions, list) or not questions:
        questions = _local_questions(topic, question_count, source_ids)
    valid = [item for item in questions[:question_count] if isinstance(item, dict) and item.get('question') and isinstance(item.get('options'), list) and len(item['options']) >= 2 and item.get('correct_answer') in item['options']]
    if not valid: raise ValueError('Assessment generation returned invalid questions.')
    with transaction.atomic():
        assessment = GeneratedTest.objects.create(student=user, subject=subject, topic=topic, difficulty=difficulty, question_count=len(valid))
        GeneratedQuestion.objects.bulk_create([GeneratedQuestion(test=assessment, order=index, question=item['question'], options=item['options'], correct_answer=item['correct_answer'], explanation=item.get('explanation', ''), source_ids=item.get('source_ids', source_ids)) for index, item in enumerate(valid)])
    return assessment, valid, bool(chunks)
