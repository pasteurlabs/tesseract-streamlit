# Using JAX with finite element methods (JAX-FEM)

In this example, you'll generate a Streamlit app from a Tesseract which models a structure and computes its compliance with finite element methods.
This is based on the example for [shape optimisation in Tesseract-JAX](https://docs.pasteurlabs.ai/projects/tesseract-jax/latest/examples/fem-shapeopt/demo.html) using JAX-FEM.
This, of course, uses `tesseract-streamlit` to automatically generate an interactive web app, this time with an interactive PyVista plot of the structure! ⚡

---

## 📥 Step 1: Download the Example Code

We've written a custom Tesseract for this example, mashing up the Design Tesseract and FEM Tesseract from the original Tesseract JAX tutorial, so clone `tesseract-streamlit` like so:

```shell
git clone --depth 1 https://github.com/pasteurlabs/tesseract-streamlit.git ~/Downloads/tesseract-streamlit
```

---

## 📦 Step 2: Install Requirements

Enter the example directory, and install the required packages:

```bash
cd ~/Documents/tesseract-streamlit/examples/jax_fem
pip install -r requirements.txt
```

---

## 🛠️ Step 3: Build and Serve the Tesseract

Use the Tesseract CLI to build and serve `jax_fem`:

```bash
tesseract build ~/Documents/tesseract-streamlit/examples/jax_fem
tesseract serve jax_fem
```

> [!NOTE]
> Make note of the `PORT` and `PROJECT ID` printed to stdout — you'll need them shortly.

---

## ⚡ Step 4: Generate and Launch the Streamlit App

With `tesseract-streamlit` installed, generate and launch the app in one step:

```bash
cd ~/Documents/tesseract-streamlit/examples/jax_fem
tesseract-streamlit --user-code udf.py "http://localhost:<PORT>"
```

This writes the app to a cache file and launches Streamlit automatically.

`udf.py` can be found in under `tesseract-streamlit/examples/jax_fem/`.
It contains a custom function that takes the Tesseract's inputs to render a PyVista plot of the design structure directly in the UI! ⚙️
Check out the [source code to see how it works](https://github.com/pasteurlabs/tesseract-streamlit/examples/jax_fem/udf.py).

> [!TIP]
> You can also skip Step 3 entirely and let `tesseract-streamlit` serve the Tesseract for you:
> ```bash
> tesseract-streamlit --from-image jax_fem --user-code udf.py
> ```

If you prefer to generate a script to run later, pass an output path:

```bash
tesseract-streamlit --user-code udf.py "http://localhost:<PORT>" app.py
streamlit run app.py
```

This will launch a web interface for submitting inputs, running the Tesseract, and visualising the results.

The form is populated from sensible defaults defined in `tesseract_api.py`.
To easily provide the input parameters for the structure itself, you can upload the `bar_params.json` file in the current directory.

---

## 🖼️ Screenshots


|     |     |
| --- | --- |
|     |     |

---

## 🧹 Step 6: Clean Up

When you're done, you can stop the Tesseract server with:

```bash
tesseract teardown <PROJECT ID>
```

---

🎉 That’s it — you've transformed a running Tesseract into a beautiful Streamlit web app with interactive plots, with minimal effort from the command line!
