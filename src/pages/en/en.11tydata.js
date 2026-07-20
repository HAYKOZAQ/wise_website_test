module.exports = {
  eleventyComputed: {
    // Keep the legacy /en/*.html URLs while emitting them from src/pages/en.
    // Note: page.fileSlug is "en" for src/pages/en/index.html, so use the
    // input filename instead.
    permalink: (data) => {
      const file = String(data.page.inputPath || "").split(/[\\/]/).pop() || "index.html";
      const slug = file.replace(/\.html$/i, "") || "index";
      return `/en/${slug}.html`;
    },
  },
};
