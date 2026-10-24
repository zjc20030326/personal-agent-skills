# Mathematical LaTeX Style Reference

Use this reference to write readable, checkable mathematical LaTeX. Preserve explicit user or document conventions when they differ. Do not change mathematical meaning merely to normalize style.

## Contents

1. Output-medium contract
2. Formula selection and punctuation
3. Fractions, operators, limits, and sums
4. Integrals and differentials
5. Sets, intervals, vectors, matrices, and operators
6. Derivation granularity
7. Frequent mistakes
8. Final checklist

## 1. Output-medium contract

Choose delimiters from the requested target artifact, not from the delivery channel or personal preference. Apply this strict priority:

1. If the user requests Markdown, Markdown-ready content, or `.md` content, use the Markdown contract `$...$` and `$$...$$`. This remains true when the Markdown source is delivered inside a chat response.
2. Otherwise, if the user requests a pure `.tex` file, a LaTeX fragment, LaTeX source, or content ready to place in `.tex`, use the `.tex` contract `$...$` and `\[...\]` or an appropriate LaTeX environment. This remains true when the `.tex` source is delivered inside a chat response.
3. Only when the user requests neither Markdown nor `.tex` output and is asking for an ordinary conversational explanation of mathematics, use the ChatGPT contract `\(...\)` and `$$...$$`.

Do not infer the target medium from the fact that Codex is replying through chat.

| Destination | Inline math | Display math |
| --- | --- | --- |
| ChatGPT response | `\(...\)` | `$$...$$` |
| Markdown file | `$...$` | `$$...$$` |
| Pure `.tex` file | `$...$` | `\[...\]` or an appropriate LaTeX environment |

Minimal examples:

```text
User: Write a Markdown-ready sentence stating that x equals 1.
Output: The value is $x=1$.
```

```text
User: Give source that can be placed in a pure .tex file.
Output: The value is $x=1$.
```

```text
User: Explain conversationally why x equals 1.
Output: The value is \(x=1\).
```

For a pure `.tex` file, use `equation`, `align`, `gather`, `matrix`, and related environments where their semantics help. Use `equation` only when a number or label is needed. Do not put Markdown fences around `.tex` output.

For Markdown files, do not use `\(...\)` or `\[...\]`; use `$...$` and `$$...$$`. Do not wrap mathematical delimiters in code ticks. Keep a display formula on its own lines:

```markdown
The sequence satisfies $a_n \to 0$.

$$
\sum\limits_{k=1}^{n} k=\dfrac{n(n+1)}{2}.
$$
```

For chat output, use `\(...\)` inline and `$$...$$` for display. For example, write `\(A\bm{x}=\bm{b}\)` in a sentence.

## 2. Formula selection and punctuation

Keep a short condition, definition, or conclusion inline when it reads naturally in its sentence, for example `$x\ne 0$`, `$r=\lVert\bm{x}\rVert$`, or `$f(0)=0$` in a Markdown file. Avoid turning isolated, very short equalities into a succession of displays.

Use display math when the expression is long, needs emphasis, contains several aligned transformations, includes a matrix, determinant, cases, system, multiple integral, or requires a number or label. Use `aligned` inside a display for a compact derivation, and use `align` in `.tex` when separate alignment and optional labels are needed.

End a display that belongs to a sentence with appropriate punctuation inside the mathematics: a comma for continuation, a period for completion, or a semicolon where it separates clauses. For example:

```latex
\[
    \det(A-\lambda I_n)=0.
\]
```

Place prose punctuation outside inline math when it punctuates the prose sentence, for example `$f$ is continuous.` In Chinese prose, follow the document's language convention; do not introduce a different punctuation system solely because math is present.

## 3. Fractions, operators, limits, and sums

Use `\dfrac{numerator}{denominator}` for every ordinary fraction. Whenever a fraction occurs in a superscript or subscript, use `\frac{numerator}{denominator}` instead. This includes exponents, ordinary symbol subscripts, and the upper or lower limits of integrals, sums, products, limits, and similar operators. For example, write `e^{-\frac{x-\mu}{s}}`, `\left(1+\frac{x^2}{n}\right)^{-\frac{n+1}{2}}`, `\int_0^{\frac{\pi}{2}}`, `\sum\limits_{k=\frac{1}{2}}^n`, and `a^{\frac{1}{n}}`. Do not use `\frac` outside superscripts or subscripts. Always include both brace pairs; never abbreviate `\dfrac{1}{2}` as `\dfrac12` or `\frac{1}{2}` as `\frac12`. Yield only when the user explicitly specifies another form or an existing document has a hard convention that must be preserved.

Use semantic operators rather than letter-by-letter roman text:

```latex
\sin x,\quad \log x,\quad \exp x,\quad \det A,\quad \ker T,\quad \operatorname{rank} A.
```

Declare a repeated custom operator in the preamble with `\DeclareMathOperator`, for example `\DeclareMathOperator{\rank}{rank}`. Do not redeclare an operator inside a fragment unless the task includes the preamble.

Write every binomial coefficient as `C_n^k`, where the lower index is the total number and the upper index is the number selected. This is the required default notation; do not use `\binom{n}{k}` or stacked parenthesized notation. For example:

```latex
C_n^k=\dfrac{n!}{k!(n-k)!}.
```

Use `\limits` for every limit and sum:

```latex
\lim\limits_{x\to 0}\dfrac{\sin x}{x}=1,
\qquad
\sum\limits_{k=1}^{n} k=\dfrac{n(n+1)}{2}.
```

TeX sets a fraction argument and every superscript and subscript one style level below its surroundings, and it sets inline math in text style. A large operator in any of those places therefore loses its display layout: `\int_0^x` moves its bounds beside a smaller integral sign, and a `\sum`, `\prod`, or `\lim` written without `\limits` does the same. Put an explicit `\displaystyle` immediately in front of such an operator, for example `$\displaystyle\lim\limits_{n\to\infty} a_n$`, `$A_n=\displaystyle\sum\limits_{k=1}^{n}a_k$`, or `\dfrac{\displaystyle\int_0^x f(t)\,\mathrm{d}t}{\displaystyle\int_0^x g(t)\,\mathrm{d}t}`; one is enough for the rest of that formula, and any existing `\limits` stays.

In a superscript or subscript, keep the operator in the smaller script size instead, exactly as a fraction there takes `\frac` rather than `\dfrac`: write `e^{\int g(x)\,\mathrm{d}x}`.

No `\displaystyle` is needed anywhere else: display math, the rows of `aligned`, `\sqrt{...}`, and `\left(...\right)` already carry the surrounding style, and a one-variable integral still takes no `\limits`.

Yield from these limit and sum defaults only when the user explicitly specifies another convention or an existing document has a hard convention that must be preserved. Do not use `\limits` as a blanket replacement for every subscripted operator.

## 4. Integrals and differentials

For a one-variable definite or improper integral, attach numerical or functional bounds directly to the integral without `\limits`:

```latex
\int_0^x f(t)\,\mathrm{d}t,
\qquad
\int_0^{+\infty} e^{-t}\,\mathrm{d}t.
```

Use a thin space before the differential and write the differential upright, such as `\,\mathrm{d}x`, `\,\mathrm{d}t`, or `\,\mathrm{d}V`. Preserve a document's existing differential macro if it has one.

For multiple, line, or surface integrals whose subscript denotes a region, curve, or surface, use `\limits`:

```latex
\iint\limits_D f(x,y)\,\mathrm{d}A,
\qquad
\iiint\limits_{\Omega} g(x,y,z)\,\mathrm{d}V,
\qquad
\int\limits_{\Gamma} \bm{F}\cdot\mathrm{d}\bm{r}.
```

Make the measure match the domain: `\mathrm{d}x` for a variable, `\mathrm{d}A` or `\mathrm{d}x\,\mathrm{d}y` for a planar region, `\mathrm{d}V` for a volume, `\mathrm{d}s` for arc length, and `\mathrm{d}S` for surface area. State iterated bounds clearly and keep their integration order consistent with the differentials.

## 5. Sets, intervals, vectors, matrices, and operators

Use `\mathbb{R}`, `\mathbb{C}`, and similar blackboard-bold symbols for standard number systems. Write every closed interval as `\lbrack a,b\rbrack`. Write half-open intervals as `\lbrack a,b)` and `(a,b\rbrack`; write an open interval as `(a,b)`.

Use a deliberate vector convention, normally `\bm{x}` when the `bm` package is available, and apply it consistently to zero vectors, gradients, and coordinates:

```latex
\bm{x}\in\mathbb{R}^n,
\qquad
\bm{0},
\qquad
\nabla f(\bm{x}).
```

Use `pmatrix`, `bmatrix`, `vmatrix`, and `cases` instead of manually typed delimiters. Keep matrix rows aligned with `&` and end all but the final row with `\\`:

```latex
\begin{pmatrix}
    a & b \\
    c & d
\end{pmatrix},
\qquad
\begin{vmatrix}
    a & b \\
    c & d
\end{vmatrix}.
```

Write matrix operations semantically: `A\bm{x}=\bm{b}`, `A^{\mathsf{T}}`, `A^{-1}`, `\det A`, and `\operatorname{tr}(A)`. Keep scalar, vector, matrix, and linear-operator symbols visually distinguishable. Use `\lVert\bm{x}\rVert` for norms when `amsmath` is available; use `\|\bm{x}\|` only if the local source already does.

## 6. Derivation granularity

Show enough intermediate work for a reader to verify the result. Do not compress a transformation that determines a final coefficient, sign, order, convergence range, boundary term, or equality condition.

For a composite Taylor expansion with cancellation, write: base expansions, substitution into the composite expressions, collection by powers, then subtraction or substitution into the target. Include an error term of sufficient order. A suitable `.tex` pattern is:

```latex
\begin{align*}
    \sin x &= x-\dfrac{x^3}{6}+\dfrac{x^5}{120}+O(x^7),\\
    \tan x &= x+\dfrac{x^3}{3}+\dfrac{2x^5}{15}+O(x^7),\\
    \sin(\tan x) &= \left(x+\dfrac{x^3}{3}+\dfrac{2x^5}{15}\right)
        -\dfrac{1}{6}\left(x+\dfrac{x^3}{3}\right)^3
        +\dfrac{x^5}{120}+O(x^7)\\
    &=x+\dfrac{x^3}{6}-\dfrac{x^5}{40}+O(x^7),\\
    \tan(\sin x) &= \left(x-\dfrac{x^3}{6}+\dfrac{x^5}{120}\right)
        +\dfrac{1}{3}\left(x-\dfrac{x^3}{6}\right)^3
        +\dfrac{2x^5}{15}+O(x^7)\\
    &=x+\dfrac{x^3}{6}-\dfrac{x^5}{40}+O(x^7).
\end{align*}
```

For a power-series calculation driven by termwise differentiation, identify the convergence condition and show the chain from the geometric series through differentiation and simplification:

```latex
\begin{aligned}
    \sum\limits_{n=1}^{\infty} nt^n
    &=t\sum\limits_{n=1}^{\infty} nt^{n-1}\\
    &=t\dfrac{\mathrm{d}}{\mathrm{d}t}
      \left(\sum\limits_{n=0}^{\infty} t^n\right)\\
    &=t\dfrac{\mathrm{d}}{\mathrm{d}t}
      \left(\dfrac{1}{1-t}\right)
      =\dfrac{t}{(1-t)^2},\qquad |t|<1.
\end{aligned}
```

Compress routine algebra only after naming the theorem, identity, or preceding result that justifies it. Expand a nonstandard step or one likely to be questioned. Do not replace a required condition or a key derivation stage with an ellipsis in final work.

## 7. Frequent mistakes

- Mixing chat delimiters with Markdown-file delimiters.
- Wrapping `$...$` or `$$...$$` in backticks.
- Using a display merely for a trivial equality that belongs in prose.
- Omitting punctuation from a sentence-level display.
- Leaving an operator as italic letters, such as `rank`, instead of `\operatorname{rank}` or a declared operator.
- Applying `\limits` to ordinary one-variable bounds, or omitting it from region-labelled multiple integrals, line integrals, or surface integrals.
- Writing `dx` as ordinary variables rather than `\,\mathrm{d}x`.
- Mixing vector conventions or using incompatible matrix dimensions.
- Giving only a final Taylor coefficient or power-series closed form when cancellation or termwise differentiation is central to the argument.
- Using `\left` and `\right` indiscriminately; use fixed delimiters when automatic sizing does not improve readability.
- Forgetting braces in exponents, subscripts, fractions, and multi-token commands.
- Writing a binomial coefficient as `\binom{n}{k}` or stacked parentheses instead of `C_n^k`.
- Using `\dfrac` or `\tfrac` for a fraction inside any superscript or subscript, including an integral, sum, product, or limit bound; use fully braced `\frac{numerator}{denominator}` there.

## 8. Final checklist

- Confirm the output medium and its delimiter pair.
- Ensure every display has balanced delimiters or environments and appropriate punctuation.
- Verify fractions, limits, sums, integrals, measures, and regions use the intended conventions.
- Verify every binomial coefficient uses `C_n^k`, with the total as the lower index and the selected number as the upper index.
- Verify closed intervals use `\lbrack...\rbrack` and half-open intervals use the corresponding `\lbrack` or `\rbrack` form.
- Check vector, matrix, operator, and norm notation for consistency and dimension plausibility.
- Check every Taylor or series derivation for sufficient intermediate steps and stated conditions.
- Preserve user macros and local conventions; mention any missing package or macro dependency.
