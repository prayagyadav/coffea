import os
import re
import argparse
import config

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i",
    "--indir",
    help="Enter the export directory path",
    type=str
)

inputs = parser.parse_args()

dir_name = inputs.indir

dir = dir_name.split('/')[0]

print("Directory: ", dir)

#template_file = 'template.tex'
#template_sty = 'template.sty'
template_file = config.template_tex
template_sty = config.template_sty

with open(template_file,'r') as tex:
    data = tex.read()

preamble = data.strip().split('\\begin{document}')[0].strip()

files_in_dir = os.listdir(dir)
tex_files = [f for f in files_in_dir if f.endswith('.tex')]
nums = {int(name.strip('.tex').split('_')[-1]):name for name in tex_files}
keys = list(nums.keys())
keys.sort()
tex_files = [nums[name] for name in keys]

print('Detected Tex files\n', tex_files)

if not os.system(f'cp {template_file} {dir}') == 0:
    raise RuntimeError(f"Failed to copy {template_file} to {dir}")
if not os.system(f'cp {template_sty} {dir}') == 0:
    raise RuntimeError(f"Failed to copy {template_sty} to {dir}")
print("Templates copied")

slides = []
for f in tex_files:
    with open(dir+'/'+f,'r') as tex:
        dat = tex.read()
    a = dat.strip().split('\\begin{document}')[-1].strip().strip('\\end{document}').strip()
    b = a.strip().strip('\\begin{frame}[allowframebreaks,fragile]').strip('\\end{frame}').strip().strip('\\pagebreak').strip()
    content = b.strip('title') .strip('% Add a bibliography block to the postdoc').strip()
    slides.append(content)

divider = '\n\n%-------------------------------------------------\n\\pagebreak\n%-------------------------------------------------\n\n'
all_slides = divider.join(slides)

final_string = preamble+'\n\n\\begin{document}\n\n\\begin{frame}[allowframebreaks,fragile]\n\n\\tiny\n\n'+all_slides+'\n\n\\end{frame}\n\n\n\n\\end{document}'

with open(dir+'/'+dir.split('_export')[0]+'_main.tex','w') as f:
    f.write(final_string)

print(dir+'/'+dir.split('_export')[0]+'_main.tex created')
