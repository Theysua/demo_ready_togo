import os
import glob

def main():
    output_file = "Goodyear_Hybrid_Knowledge_Base.md"
    md_files = sorted(glob.glob("markdown_output/page_*.md"))
    
    if not md_files:
        print("No markdown files found in markdown_output/")
        return
        
    print(f"Found {len(md_files)} markdown files. consolidating...")
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("# Goodyear Tyre Product Catalogue 2023\n\n")
        
        for file in md_files:
            try:
                with open(file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    
                    # Optional: Add a page break marker or header for each original page
                    page_num = os.path.basename(file).split('_')[1].split('.')[0]
                    outfile.write(f"\n\n---\n\n## Page {page_num}\n\n")
                    
                    outfile.write(content)
                    outfile.write("\n")
            except Exception as e:
                print(f"Error processing {file}: {e}")
                
    print(f"Success! Consolidated all pages into {output_file}")

if __name__ == "__main__":
    main()
