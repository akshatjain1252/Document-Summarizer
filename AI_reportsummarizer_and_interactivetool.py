import os
import docx
from transformers import pipeline
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader


def read_text_from_file(file_path):
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == '.docx':
        doc = docx.Document(file_path)
        text = " ".join([paragraph.text for paragraph in doc.paragraphs])
    elif extension == '.pdf':
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            text = " ".join([pdf_reader.pages[page_num].extract_text() for page_num in range(len(pdf_reader.pages))])
    elif extension == '.txt':
        with open(file_path, 'r', encoding='utf-8') as txt_file:
            text = txt_file.read()
    else:
        raise ValueError(f"Unsupported file type: {extension}")

    return text


def write_summary_to_pdf(summary, output_file, left_margin=50, right_margin=550, line_spacing=12):
    with open(output_file, 'wb') as pdf_file:
        pdf = canvas.Canvas(pdf_file)
        pdf.setFont("Helvetica", 12)

        # Set the alignment to left
        pdf.setFont("Helvetica", 10)

        # Split the summary into lines to fit within the specified width
        words = summary.split()
        lines = []
        current_line = []
        current_line_length = 0

        for word in words:
            word_length = pdf.stringWidth(word, "Helvetica", 10)

            if current_line_length + word_length < right_margin - left_margin:
                current_line.append(word)
                current_line_length += word_length + pdf.stringWidth(" ", "Helvetica", 10)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_line_length = word_length + pdf.stringWidth(" ", "Helvetica", 10)

        if current_line:
            lines.append(' '.join(current_line))

        # Draw each line in the summary with left alignment and uniform space between words
        y_position = 750  # Starting y position
        for line in lines:
            # Draw each line starting from left margin
            pdf.drawString(left_margin, y_position, line)
            y_position -= line_spacing  # Update y position for the next line

            # Start a new page if the summary goes beyond the page boundary
            if y_position < 50:
                pdf.showPage()
                y_position = 750  # Reset y position for the new page

        pdf.save()


# Load the summarization pipeline
summarizer = pipeline("summarization")

# Get user input for the input file name
input_filename = input("Enter the name of your input file: ")

# Combine the filename with the current working directory to form the input file path
input_file = os.path.join(os.getcwd(), input_filename)

# Read input file
text = read_text_from_file(input_file)

# Get user input for the desired word count
desired_word_count = int(input("Enter the desired word count for the summary: "))

# Set minimum length constraint for summarization
min_length = 100
max_length = max(2 * desired_word_count, min_length)

# Calculate the number of chunks based on the chunk size
chunk_size = 500  # Adjust this based on your needs
num_chunks = (len(text) + chunk_size - 1) // chunk_size

# Summarize each chunk and concatenate the summaries
summaries = []

for i in range(num_chunks):
    start_idx = i * chunk_size
    end_idx = min((i + 1) * chunk_size, len(text))
    chunk = text[start_idx:end_idx]

    summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
    summaries.append(summary[0]['summary_text'])

# Concatenate the summarized chunks
final_summary = ' '.join(summaries)

# Trim the summary to match the desired word count exactly
words = final_summary.split()[:desired_word_count]
truncated_summary = ' '.join(words)

# Get user input for the output file name
output_filename = input("Enter the name of your output file (with .pdf extension): ")

# Combine the filename with the current working directory to form the output file path
output_file = os.path.join(os.getcwd(), output_filename)

# Write summary to a new PDF file using reportlab
write_summary_to_pdf(truncated_summary, output_file)

print("Summary saved successfully.")
