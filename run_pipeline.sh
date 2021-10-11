#!/bin/bash

# Wrapper for juno assembly pipeline

set -euo pipefail

#----------------------------------------------#
# User parameters
input_dir="${1%/}"
output_dir="${2%/}"
PROJECT_NAME="${irods_input_projectID}" # This should be an environment variable

#----------------------------------------------#
# Create/update necessary environments
PATH_MAMBA_YAML="envs/mamba.yaml"
PATH_MASTER_YAML="envs/master_env.yaml"
MAMBA_NAME=$(head -n 1 ${PATH_MAMBA_YAML} | cut -f2 -d ' ')
MASTER_NAME=$(head -n 1 ${PATH_MASTER_YAML} | cut -f2 -d ' ')

echo -e "\nUpdating necessary environments to run the pipeline..."

# Removing strict mode because it sometimes breaks the code for 
# activating an environment and for testing whether some variables
# are set or not
set +euo pipefail 
bash install_juno_assembly.sh

#----------------------------------------------#
# Run the pipeline

case $PROJECT_NAME in
  adhoc|rogas|svgasuit|bsr_rvp)
    GENUS_ALL="NotProvided"
    ;;
  dsshig|svshig)
    GENUS_ALL="Shigella"
    ;;
  salm|svsalent|svsaltyp|vdl_salm)
    GENUS_ALL="Salmonella"
    ;;
  svlismon|vdl_list)
    GENUS_ALL="Listeria"
    ;;
  svstec|vdl_ecoli|vdl_stec)
    GENUS_ALL="Escherichia"
    ;;
  campy|vdl_campy)
    GENUS_ALL="Campylobacter"
    ;;
  *)
    GENUS_ALL="NotProvided"
    ;;
esac


echo -e "\nRun pipeline..."

if [ ! -z ${irods_runsheet_sys__runsheet__lsf_queue} ]; then
    QUEUE="${irods_runsheet_sys__runsheet__lsf_queue}"
else
    QUEUE="bio"
fi

set -euo pipefail

if [ "${GENUS_ALL}" == "NotProvided" ]; then
    python juno_assembly.py --queue "${QUEUE}" -i "${input_dir}" -o "${output_dir}"
    result=$?
elif [ ${irods_input_projectID} == "refsamp" ]; then
    GENUS_FILE=`realpath $(find ../ -type f -name genus_sheet_refsamp.xlsx)`
    python juno_assembly.py --queue "${QUEUE}" -i "${input_dir}" -o "${output_dir}" --metadata "${GENUS_FILE}"
    result=$?
else
    python juno_assembly.py --queue "${QUEUE}" -i "${input_dir}" -o "${output_dir}" --genus "${GENUS_ALL}"
    result=$?
fi

# Propagate metadata
SEQ_KEYS=
SEQ_ENV=`env | grep irods_input_sequencing`
for SEQ_AVU in ${SEQ_ENV}
do
    SEQ_KEYS="${SEQ_KEYS} ${SEQ_AVU%%=*}"
done

for key in $SEQ_KEYS irods_input_illumina__Flowcell irods_input_illumina__Instrument \
    irods_input_illumina__Date irods_input_illumina__Run_number irods_input_illumina__Run_Id
do
    if [ ! -z ${!key} ] ; then
        attrname=${key:12}
        attrname=${attrname/__/::}
        echo "${attrname}: '${!key}'" >> ${OUTPUTDIR}/metadata.yml
    fi
done

exit ${result}
# Produce svg with rules
# snakemake --config sample_sheet=config/sample_sheet.yaml \
#             --configfiles config/pipeline_parameters.yaml config/user_parameters.yaml \
#             -j 1 --use-conda \
#             --rulegraph | dot -Tsvg > files/DAG.svg
