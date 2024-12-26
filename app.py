import ifcopenshell.util.element as Element
import streamlit as st
import pandas as pd
import ifcopenshell
import tempfile

st.set_page_config(layout="wide")


def generate_excel_download_link(df: pd.DataFrame, btn_name: str):
    # Use a temporary file to save the dataframe as an Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        df.to_excel(tmp_file.name, index=False, engine="openpyxl")
        tmp_file_path = tmp_file.name

    with open(tmp_file_path, "rb") as file:
        btn = st.download_button(
            label=btn_name,
            data=file,
            file_name="ifc_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return btn


def get_objects_data_by_class(file: ifcopenshell.file, class_type: str):
    def process_property_sets(psets, pset_attributes):
        for pset_name, pset_data in psets.items():
            pset_attributes.update(
                f"{pset_name}.{prop_name}" for prop_name in pset_data
            )
        return pset_attributes

    objects = file.by_type(class_type)
    objects_data = []
    pset_attributes = set()

    for object in objects:
        pset_attributes = process_property_sets(
            Element.get_psets(object, qtos_only=True), pset_attributes
        )
        pset_attributes = process_property_sets(
            Element.get_psets(object, psets_only=True), pset_attributes
        )

        objects_data.append(
            {
                "GlobalId": object.GlobalId,
                "Class": object.is_a(),
                "Name": object.Name,
                "Tag": object.Tag,
                "Type": getattr(Element.get_type(object), "Name", ""),
                "QuantitySets": Element.get_psets(object, qtos_only=True),
                "PropertySets": Element.get_psets(object, psets_only=True),
            }
        )
    return objects_data, list(pset_attributes)


def get_attribute_value(object_data, attribute):
    if "." not in attribute:
        return object_data.get(attribute)

    pset_name, prop_name = attribute.split(".", 1)
    for set_type in ("PropertySets", "QuantitySets"):
        if pset := object_data.get(set_type, {}).get(pset_name):
            return pset.get(prop_name)
    return None


def create_pandas_dataframe(data, pset_attributes):
    attributes = ["GlobalId", "Class", "Name", "Type"] + pset_attributes
    return pd.DataFrame(
        [
            [get_attribute_value(obj_data, attr) for attr in attributes]
            for obj_data in data
        ],
        columns=attributes,
    )


def sidebar_opt(column_names: list):
    ignore_columns = []

    st.sidebar.divider()
    chechk_all = st.sidebar.checkbox("Check all boxes", value=True)
    st.sidebar.divider()

    for col_name in column_names:
        if not st.sidebar.checkbox(col_name, value=chechk_all):
            ignore_columns.append(col_name)

    return ignore_columns


def create_unique_count_df(dataframe: pd.DataFrame, column_name: str):
    value_counts = dataframe[column_name].value_counts().reset_index()
    value_counts.columns = [column_name, "Count"]

    return value_counts


def process_df(ifc):
    data, pset_attributes = get_objects_data_by_class(ifc, "IfcBuildingElement")
    df = create_pandas_dataframe(data, pset_attributes)
    return df.drop(columns=sidebar_opt(df.columns)).reset_index(drop=True)


def run():
    st.title("Exported IFC parts to excel")
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload exported ifc from tekla",
        type=["ifc"],
    )

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".ifc"):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_file_path = tmp_file.name

            with st.spinner("Reading the IFC file..."):
                exported_ifc = ifcopenshell.open(tmp_file_path)

            st.success("IFC file loaded successfully!")

            # --- IFC DATA ---
            st.divider()
            clean_df = process_df(exported_ifc)
            st.header("IFC data")
            st.dataframe(clean_df)
            generate_excel_download_link(clean_df, "Download data as Excel")

            # --- COUNT DETAILS ---
            st.divider()
            st.header("Count of details")
            count_data_column_name = st.selectbox(
                "Choose a column to count", clean_df.columns
            )

            if len(clean_df.columns) == 0:
                st.warning("Choose column to count")
                st.stop()

            count_of_details = create_unique_count_df(clean_df, count_data_column_name)
            st.dataframe(count_of_details)
            generate_excel_download_link(count_of_details, "Download count as Excel")

            st.divider()

        else:
            st.error(
                "The uploaded file is not an IFC file. Please upload a file with .ifc extension."
            )

            st.stop()


if __name__ == "__main__":
    run()
