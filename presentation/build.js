/**
 * Build script for "Death to PowerPoint" presentation
 * Converts HTML slides to PowerPoint using html2pptx
 */

const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');
const path = require('path');

async function build() {
  console.log('Building presentation...\n');

  // Create presentation with 10" x 7.5" layout (standard)
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_WIDE';  // 13.33" x 7.5"

  // Override to 10" x 7.5" to match HTML
  pptx.defineLayout({ name: 'CUSTOM', width: 10, height: 7.5 });
  pptx.layout = 'CUSTOM';

  pptx.author = 'Pravin Vasudevan';
  pptx.title = 'Death to PowerPoint';
  pptx.subject = 'How I Ship Customer Demos in Hours, Not Weeks';
  pptx.company = 'Databricks';

  // Slides in order
  const slides = [
    '01-title.html',
    '02-problem.html',
    '03-paradigm.html',
    '04-stack.html',
    '05-workflow.html',
    '06-demo-preview.html',
    '07-code-pattern.html',
    '08-patterns.html',
    '09-pitfalls.html',
    '10-results.html',
    '11-getting-started.html',
    '12-questions.html'
  ];

  const slidesDir = path.join(__dirname, 'slides');

  for (const slideFile of slides) {
    const slidePath = path.join(slidesDir, slideFile);
    console.log(`  Converting ${slideFile}...`);

    try {
      await html2pptx(slidePath, pptx);
    } catch (error) {
      console.error(`  ERROR in ${slideFile}: ${error.message}`);
      process.exit(1);
    }
  }

  // Save output
  const outputPath = path.join(__dirname, '..', 'death_to_powerpoint.pptx');
  await pptx.writeFile({ fileName: outputPath });

  console.log(`\nPresentation saved to: ${outputPath}`);
  console.log(`Total slides: ${slides.length}`);
}

build().catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
