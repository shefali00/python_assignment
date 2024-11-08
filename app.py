from flask import Flask, request, jsonify
from google.generativeai import configure, GenerativeModel
import os
from functools import wraps
import json

app = Flask(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Error handling if API key is not set
if GEMINI_API_KEY is None:
    raise ValueError("API Key not set. Please set GOOGLE_API_KEY in environment variables.")

# Configure Google AI API


def validate_input(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = request.get_json()

            # Check if required fields exist
            if not data or 'company_name' not in data or 'transcript_text' not in data:
                return jsonify({
                    'error': 'Missing required fields. Please provide company_name and transcript_text.'
                }), 400

            # Check if fields are empty
            if not data['company_name'].strip() or not data['transcript_text'].strip():
                return jsonify({
                    'error': 'Company name and transcript text cannot be empty.'
                }), 400

            # Check transcript length (approximate token count)
            if len(data['transcript_text'].split()) > 20000:
                return jsonify({
                    'error': 'Transcript text exceeds maximum length of 20,000 tokens.'
                }), 400

            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': f'Invalid request format: {str(e)}'
            }), 400
    return wrapper

def get_category_summary(transcript, category, company_name):
    """Generate summary for a specific category using Gemini."""
    prompts = {
        'financial_performance': f"Summarize the financial performance from this earnings call transcript for {company_name}. Focus on key metrics, revenue, profit, and overall financial health. Keep it concise and factual.",
        'market_dynamics': f"Summarize the market dynamics mentioned in this earnings call transcript for {company_name}. Include market trends, demand shifts, and competitive landscape. Be concise and specific.",
        'expansion_plans': f"Extract and summarize any expansion or growth plans mentioned in this earnings call transcript for {company_name}. Focus on future initiatives and strategic plans. Be concise.",
        'environmental_risks': f"Summarize any environmental risks, sustainability initiatives, or ESG concerns mentioned in this earnings call transcript for {company_name}. Be concise and specific.",
        'regulatory_or_policy_changes': f"Summarize any regulatory or policy changes mentioned in this earnings call transcript for {company_name} that affect the company. Be concise and specific."
    }

    try:
        response = model.generate_content(
            f"{prompts[category]}\n\nTranscript:\n{transcript}"
        )
        return response.text if response.text else "No relevant information found."
    except Exception as e:
        return f"Error generating summary for {category}: {str(e)}"

@app.route('/earnings_transcript_summary', methods=['POST'])
@validate_input
def summarize_transcript():
    try:
        data = request.get_json()
        company_name = data['company_name']
        transcript_text = data['transcript_text']

        # Generate summaries for each category
        summary = {
            'company_name': company_name,
            'financial_performance': get_category_summary(transcript_text, 'financial_performance', company_name),
            'market_dynamics': get_category_summary(transcript_text, 'market_dynamics', company_name),
            'expansion_plans': get_category_summary(transcript_text, 'expansion_plans', company_name),
            'environmental_risks': get_category_summary(transcript_text, 'environmental_risks', company_name),
            'regulatory_or_policy_changes': get_category_summary(transcript_text, 'regulatory_or_policy_changes', company_name)
        }

        return jsonify(summary), 200

    except Exception as e:
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500

@app.route('/', methods=['GET'])
def home():
    return '''
    <h1>Earnings Call Transcript Summary API</h1>
    <p>Use POST /earnings_transcript_summary to analyze earnings call transcripts.</p>
    <p>See documentation for details on request/response format.</p>
    '''


    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
