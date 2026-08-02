from fpdf import FPDF
import pandas as pd
import os

class OpportunityPDF(FPDF):

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "African Youth Opportunities Report", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def generate_pdf(csv_file="opportunities.csv",
                 output_file="opportunities.pdf"):

    if not os.path.exists(csv_file):
        return None

    df = pd.read_csv(csv_file)

    pdf = OpportunityPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)

    for _, row in df.iterrows():

        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 7, str(row["title"]))

        pdf.set_font("Helvetica", "", 10)

        pdf.multi_cell(
            0,
            6,
            f"Organization: {row['organization']}"
        )

        pdf.multi_cell(
            0,
            6,
            f"Type: {row['type']}"
        )

        pdf.multi_cell(
            0,
            6,
            f"Deadline: {row['deadline']}"
        )

        pdf.multi_cell(
            0,
            6,
            f"Source: {row['source']}"
        )

        pdf.multi_cell(
            0,
            6,
            f"Official Link: {row['link']}"
        )

        pdf.multi_cell(
            0,
            6,
            f"Description: {row['description']}"
        )

        pdf.line(
            10,
            pdf.get_y(),
            200,
            pdf.get_y()
        )

        pdf.ln(4)

    pdf.output(output_file)

    return output_file


if __name__ == "__main__":

    generate_pdf()
