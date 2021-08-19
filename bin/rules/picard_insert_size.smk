#############################################################################
##### Scaffold analyses: QUAST, CheckM, picard, bbmap and QC-metrics    #####
#############################################################################

rule picard_insert_size:
    input:
        fasta=OUT + "/de_novo_assembly_filtered/{sample}.fasta",
        pR1=OUT + "/clean_fastq/{sample}_pR1.fastq.gz",
        pR2=OUT + "/clean_fastq/{sample}_pR2.fastq.gz"
    output:
        bam=temp(OUT + "/qc_de_novo_assembly/insert_size/{sample}_sorted.bam"),
        bam_bai=temp(OUT + "/qc_de_novo_assembly/insert_size/{sample}_sorted.bam.bai"),
        txt=OUT + "/qc_de_novo_assembly/insert_size/{sample}_insert_size_metrics.txt",
        ann=temp(OUT + "/de_novo_assembly_filtered/{sample}.fasta.ann"),
        amb=temp(OUT + "/de_novo_assembly_filtered/{sample}.fasta.amb"),
        bwt=temp(OUT + "/de_novo_assembly_filtered/{sample}.fasta.bwt"),
        pac=temp(OUT + "/de_novo_assembly_filtered/{sample}.fasta.pac"),
        sa=temp(OUT + "/de_novo_assembly_filtered/{sample}.fasta.sa"),
        pdf=OUT + "/qc_de_novo_assembly/insert_size/{sample}_insert_size_histogram.pdf"
    conda:
        "../../envs/scaffold_analyses.yaml"
    container:
        "docker://quay.io/biocontainers/picard:2.25.7--hdfd78af_0"
    log:
        OUT + "/log/picard_insert_size/picard_insert_size_{sample}.log"
    threads: config["threads"]["picard"],
    resources: mem_gb=config["mem_gb"]["picard"]
    shell:
        """
bwa index {input.fasta} > {log} 2>&1

bwa mem -t {threads} {input.fasta} \
{input.pR1} \
{input.pR2} 2>> {log} |\

samtools view -@ {threads} -uS - 2>> {log} |\
samtools sort -@ {threads} - -o {output.bam} >> {log} 2>&1

samtools index -@ {threads} {output.bam} >> {log} 2>&1

picard -Dpicard.useLegacyParser=false CollectInsertSizeMetrics \
-I {output.bam} \
-O {output.txt} \
-H {output.pdf} >> {log} 2>&1
        """
