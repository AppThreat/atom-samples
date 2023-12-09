param([array]$slice_types = @("usages", "reachables"), [array]$langs = @("java", "python", "javascript"), [string]$output_dir = ".", [string]$repo_dir = "src_repos")

function build_args
{
    [CmdletBinding()]
    param()

    $parser = New-Object System.Management.Automation.PSObject
    $parser | Add-Member -MemberType NoteProperty -Name "description" -Value "Generate Atom Samples"
    $parser | Add-Member -MemberType NoteProperty -Name "slice_types" -Value @("usages", "reachables")
    $parser | Add-Member -MemberType NoteProperty -Name "langs" -Value @("java", "python", "javascript")
    $parser | Add-Member -MemberType NoteProperty -Name "output_dir" -Value $output_dir
    $parser | Add-Member -MemberType NoteProperty -Name "repo_dir" -Value $repo_dir

    return $parser
}

function generate
{

    $repositories = @(@("apollo", "https://github.com/apolloconfig/apollo.git", "java"), @("karate", "https://github.com/karatelabs/karate.git", "java"), @("piggymetrics", "https://github.com/sqshq/piggymetrics.git", "java"), @("retrofit", "https://github.com/square/retrofit.git", "java"), @("axios", "https://github.com/axios/axios.git", "javascript"), @("videojs", "https://github.com/videojs/video.js.git", "javascript"), @("sequelize", "https://github.com/sequelize/sequelize.git", "javascript"), @("ava", "https://github.com/avajs/ava.git", "javascript"), @("spaCy", "https://github.com/explosion/spaCy.git", "python"), @("scrapy", "https://github.com/scrapy/scrapy.git", "python"), @("pynguin", "https://github.com/se2p/pynguin.git", "python"), @("tinydb", "https://github.com/msiemens/tinydb.git", "python"), @("tornado", "https://github.com/tornadoweb/tornado.git", "python")
    )


    foreach ($repo in $repositories)
    {
        if ( $langs.Contains($repo[2]))
        {
            $pname = $repo[0]
            $purl = $repo[1]
            $ptype = $repo[2]
            git clone $purl $repo_dir/$ptype/$pname

            foreach ($stype in $slice_types)
            {
                $fname = $pname + "-" + $stype + ".json"
                Write-Host "Generating "$stype" slice for "$pname" at "$output_dir/$ptype/$fname
                atom $stype -l $ptype -o $repo_dir/$ptype/$pname/$pname.atom -s $output_dir/$ptype/$fname $repo_dir/$ptype/$pname
            }
        }
    }
}

$args = build_args

generate