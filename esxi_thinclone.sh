# Adapted from https://github.com/pddenhar/esxi-linked-clone
# Jedadiah Casey, @Wax_Trax, neckercube.com
# This script assumes the INFOLDER, vmx and vmdk files have the same name

set -e

readonly NUMARGS=$#
readonly INFOLDER=$1
readonly OUTFOLDER=$2

makeandcopy() {
  mkdir "$OUTFOLDER"
  cp "$INFOLDER"/"$INFOLDER".vmx "$OUTFOLDER"/

  cd "$INFOLDER"

  # Skip -flat and account for multiple VMDKs
  for f in *[!-][!f][!l][!a][!t].vmdk
  do
    vmkfstools -i "$f" ../"$OUTFOLDER"/"$f" -d thin
  done

  cd ..
}

main() {
  if [ $NUMARGS -le 1 ]
  then
    usage
    exit 1
  fi

  if echo "$INFOLDER" | grep "[[:space:]]"
  then
    echo '$INFOLDER cannot contain spaces'
    exit 1
  fi

  if echo "$INFOLDER" | grep "/"
  then
    echo '$INFOLDER cannot contain slashes'
    exit 1
  fi

  makeandcopy

  local fullbasepath=$(readlink -f "$INFOLDER")/
  cd "$OUTFOLDER"/

  # Delete swap file line, will be auto recreated
  sed -i '/sched.swap.derivedName/d' ./*.vmx

  # Change display name config value
  sed -i -e '/displayName =/ s/= .*/= "'$OUTFOLDER'"/' ./*.vmx

  # Force creation of a fresh UUID for the VM.
  sed -i '/uuid.location/d' ./*.vmx
  sed -i '/uuid.bios/d' ./*.vmx

  # Delete machine id
  sed -i '/machine.id/d' *.vmx

  # Add machine id
  sed -i -e "\$amachine.id=$OUTFOLDER" *.vmx

}

main